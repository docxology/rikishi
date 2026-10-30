import com.articulate.sigma.KB;
import com.articulate.sigma.KBmanager;
import com.articulate.sigma.KButilities;
import com.articulate.sigma.trans.TPTPGenerationManager;
import com.articulate.sigma.tp.e.EProver;
import com.articulate.sigma.tp.ATPResult;
import com.articulate.sigma.tp.ProverTimeoutException;
import com.articulate.sigma.tp.Vampire;
import org.json.simple.JSONObject;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.io.File;
import java.util.LinkedHashMap;
import java.util.Map;

public class RikishiQuery {
    private static final String VAMPIRE_OPTIONS = "--proof tptp --mode casc";

    private static final class CompatibleVampire extends Vampire {
        private boolean submitted = false;

        CompatibleVampire(KB kb, int timeout) {
            super(kb, "tptp", "CUSTOM", false, timeout, 1);
        }

        @Override
        public void run(File problem) throws Exception {
            if (submitted) {
                throw new IllegalArgumentException("Repeated Vampire submission is unsupported");
            }
            submitted = true;
            super.runCustom(problem);
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 6 || !(args[0].equals("-e") || args[0].equals("-v"))
                || !args[1].equals("-r") || !args[2].equals("--timeout")
                || !args[4].equals("--ask") || !args[3].matches("[1-9][0-9]*")
                || Integer.parseInt(args[3]) > 300) {
            throw new IllegalArgumentException("Expected -e|-v -r --timeout 1..300 --ask QUERY");
        }
        if (args[0].equals("-v") && !VAMPIRE_OPTIONS.equals(System.getenv("VAMPIRE_OPTS"))) {
            throw new IllegalArgumentException("Unsupported Vampire invocation options");
        }
        TPTPGenerationManager.setSkipBackgroundGeneration(true);
        try {
            Path profile = Path.of(System.getenv("SIGMA_HOME"));
            KBmanager.configuration.setPreference("baseDir", profile.toString());
            KBmanager.configuration.setPreference("kbDir", profile.resolve("KBs").toString());
            KBmanager.configuration.setPreference("sumoDir", profile.resolve("KBs").toString());
            KBmanager.configuration.setPreference("graphDir", profile.resolve("graph").toString());
            KBmanager.configuration.setPreference("inferenceTestDir", profile.resolve("KBs/tests").toString());
            KBmanager.getMgr().initializeOnce(KBmanager.configuration);
            KB kb = KBmanager.getMgr().getKB(KBmanager.getMgr().getDefaultKbName());
            if (kb == null) {
                throw new IllegalStateException("Sigma did not load a knowledge base");
            }
            TPTPGenerationManager.generateFOFToPath(kb, Path.of(
                KBmanager.configuration.getKbDir(), kb.name + ".tptp"));
            KBmanager.configuration.setPreference(
                args[0].equals("-e") ? "eproverExec" : "vampireExec",
                System.getenv("RIKISHI_PROVER_ADAPTER"));
            ATPResult result;
            if (args[0].equals("-e")) {
                EProver prover = new EProver(kb, "tptp", Integer.parseInt(args[3]), 1);
                prover.askEProver(args[5]);
                result = prover.getResult();
            } else {
                Vampire prover = new CompatibleVampire(kb, Integer.parseInt(args[3]));
                try {
                    prover.askVampire(args[5]);
                } catch (ProverTimeoutException timeout) {
                    if (prover.getResult() == null) throw timeout;
                    System.err.println(timeout.getMessage());
                }
                result = prover.getResult();
            }
            if (result == null) {
                throw new IllegalStateException("Sigma did not submit a prover problem");
            }
            result.getStdout().forEach(System.out::println);
            result.getStderr().forEach(System.err::println);
            Map<String, Object> report = new LinkedHashMap<>();
            report.put("invocation_id", System.getenv("RIKISHI_INVOCATION_ID"));
            report.put("status", result.getSzsStatus().getTptpName());
            report.put("atp_returncode", result.getExitCode());
            report.put("stdout_lines", result.getStdout().size());
            report.put("capture", Path.of(System.getenv("RIKISHI_ATP_CAPTURE")).getFileName()
                + "/capture.json");
            Files.writeString(Path.of(System.getenv("RIKISHI_ATP_RESULT")),
                JSONObject.toJSONString(report), StandardOpenOption.CREATE_NEW);
        } finally {
            KButilities.shutDownExecutorService();
        }
    }
}
