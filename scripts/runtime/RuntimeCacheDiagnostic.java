import com.articulate.sigma.KB;
import com.articulate.sigma.KBcache;
import com.articulate.sigma.KIF;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public class RuntimeCacheDiagnostic {
    public static void main(String[] args) throws Exception {
        for (boolean parentIsPartial : new boolean[]{false, true}) {
            KB kb = new KB("CacheDiagnostic", args[0]);
            KIF kif = new KIF();
            kif.filename = args[0] + "/cache-diagnostic.kif";
            for (String statement : new String[]{
                "(subrelation path eventPartlyLocated)",
                "(instance path TotalValuedRelation)",
                parentIsPartial ? "(instance eventPartlyLocated PartialValuedRelation)"
                    : "(instance eventPartlyLocated Relation)"
            }) {
                String error = kif.parseStatement(statement);
                if (error != null) throw new IllegalStateException(error);
            }
            kb.addConstituentInfoAST(kif);
            kb.kbCache = new KBcache(kb);
            kb.kbCache.insts.add("path");
            kb.kbCache.instTransRels.add("subrelation");
            Map<String, Set<String>> subrelations = new HashMap<>();
            subrelations.put("path", new HashSet<>(Set.of("eventPartlyLocated")));
            kb.kbCache.parents.put("subrelation", subrelations);
            kb.kbCache.buildTransInstOf();
            Set<String> types = kb.kbCache.instanceOf.get("path");
            if (!types.contains("TotalValuedRelation")
                    || types.contains("PartialValuedRelation") != parentIsPartial) {
                throw new AssertionError("Unexpected cache inheritance: " + types);
            }
            System.out.println("parentPartial=" + parentIsPartial + "; pathPartial="
                + types.contains("PartialValuedRelation") + "; pathTotal="
                + types.contains("TotalValuedRelation"));
        }
    }
}
