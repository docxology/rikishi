import com.articulate.sigma.KB;
import com.articulate.sigma.KBmanager;
import com.articulate.sigma.KButilities;
import com.articulate.sigma.trans.TPTPGenerationManager;
import com.articulate.sigma.tp.e.EProver;
import com.articulate.sigma.tp.ATPResult;
import com.articulate.sigma.tp.Vampire;
import org.json.simple.JSONObject;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.LinkedHashMap;
import java.util.Map;

public class RikishiQuery {
    public static void main(String[] args) throws Exception {
        TPTPGenerationManager.setSkipBackgroundGeneration(true);
        try {
            KBmanager.getMgr().initializeOnce();
            KB kb = KBmanager.getMgr().getKB(KBmanager.getMgr().getDefaultKbName());
            if (kb == null) {
                throw new IllegalStateException("Sigma did not load a knowledge base");
            }
            TPTPGenerationManager.generateFOFToPath(kb, Path.of(
                KBmanager.configuration.getKbDir(), kb.name + ".tptp"));
            ATPResult result;
            if (args[0].equals("-e")) {
                EProver prover = new EProver(kb, "tptp", Integer.parseInt(args[3]), 1);
                prover.askEProver(args[5]);
                result = prover.getResult();
            } else {
                Vampire prover = new Vampire(kb, "tptp", "casc", false, Integer.parseInt(args[3]), 1);
                prover.askVampire(args[5]);
                result = prover.getResult();
            }
            if (result == null) {
                throw new IllegalStateException("Sigma did not submit a prover problem");
            }
            result.getStdout().forEach(System.out::println);
            result.getStderr().forEach(System.err::println);
            Map<String, Object> report = new LinkedHashMap<>();
            report.put("status", result.getSzsStatus().getTptpName());
            report.put("atp_returncode", result.getExitCode());
            report.put("stdout_lines", result.getStdout().size());
            report.put("stderr", result.getStderr());
            Files.writeString(Path.of(System.getenv("RIKISHI_ATP_RESULT")),
                JSONObject.toJSONString(report), StandardOpenOption.CREATE_NEW);
        } finally {
            KButilities.shutDownExecutorService();
        }
    }
}
