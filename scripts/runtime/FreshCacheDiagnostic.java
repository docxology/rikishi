import com.articulate.sigma.Formula;
import com.articulate.sigma.KB;
import com.articulate.sigma.KBcache;
import com.articulate.sigma.KBmanager;
import com.articulate.sigma.KIF;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import org.json.simple.JSONValue;

/** Observe an isolated, source-ingested KB. Never seed or alter cache maps. */
public final class FreshCacheDiagnostic {
    private static Set<String> directTypes(KB kb, String term) {
        Set<String> result = new TreeSet<>();
        for (Formula formula : kb.askWithRestriction(0, "instance", 1, term)) {
            if (!formula.isCached()) result.add(formula.getStringArgument(2));
        }
        return result;
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("workspace input result required");
        Path workspace = Path.of(args[0]).toRealPath();
        Path input = Path.of(args[1]).toRealPath();
        Path result = Path.of(args[2]).toAbsolutePath().normalize();
        if (!input.startsWith(workspace) || !result.startsWith(workspace)
                || Files.exists(result) || !workspace.resolve("sigma").toString().equals(System.getenv("SIGMA_HOME"))) {
            throw new IllegalArgumentException("fresh workspace containment required");
        }
        KB kb = new KB("FreshCache", workspace.resolve("sigma/KBs").toString());
        if (!KBmanager.configuration.isCache()) throw new IllegalStateException("cache must be enabled");
        KIF kif = new KIF();
        kif.readFile(input.toString());
        if (!kif.errorSet.isEmpty() || kif.formulaMap.isEmpty()) {
            throw new IllegalArgumentException("KIF parse failed: " + kif.errorSet);
        }
        kb.addConstituentInfoAST(kif);
        Set<String> direct = directTypes(kb, "path");
        Set<String> parent = directTypes(kb, "eventPartlyLocated");
        int sourceCount = kb.formulaMap.size();
        kb.kbCache = new KBcache(kb);
        kb.kbCache.buildCaches();
        if (!kb.kbCache.initialized || !kb.errors.isEmpty() || !KBcache.errors.isEmpty()) {
            throw new IllegalStateException("cache failed: " + kb.errors + KBcache.errors);
        }
        Set<String> cached = new TreeSet<>(kb.kbCache.getParentClassesOfInstance("path"));
        Set<String> generated = new TreeSet<>(cached);
        generated.removeAll(direct);
        Map<String, String> generatedSources = new LinkedHashMap<>();
        for (String type : generated) {
            Formula formula = kb.formulaMap.get("(instance path " + type + ")");
            if (formula == null || !formula.isCached()) {
                throw new IllegalStateException("missing generated formula for " + type);
            }
            generatedSources.put(type, formula.sourceFile);
        }
        Map<String, Object> observation = new LinkedHashMap<>();
        observation.put("schema_version", 1);
        observation.put("source_formula_count", sourceCount);
        observation.put("formula_count_after_build", kb.formulaMap.size());
        observation.put("direct_path", new ArrayList<>(direct));
        observation.put("direct_parent", new ArrayList<>(parent));
        observation.put("cached_path", new ArrayList<>(cached));
        observation.put("generated_path", new ArrayList<>(generated));
        observation.put("generated_sources", generatedSources);
        observation.put("parent_partial_inheritable", kb.kbCache.subclassOf("PartialValuedRelation", "InheritableRelation"));
        observation.put("instance_transitive_relations", new ArrayList<>(new TreeSet<>(kb.kbCache.instTransRels)));
        observation.put("subrelation_parents", new ArrayList<>(new TreeSet<>(kb.kbCache.parents.getOrDefault("subrelation", Map.of()).getOrDefault("path", Set.of()))));
        observation.put("parse_warnings", new ArrayList<>(new TreeSet<>(kif.warningSet)));
        observation.put("semantic_validation", false);
        Files.writeString(result, JSONValue.toJSONString(observation) + "\n", StandardOpenOption.CREATE_NEW);
    }
}
