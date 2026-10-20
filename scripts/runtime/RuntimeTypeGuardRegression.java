import com.articulate.sigma.FormulaPreprocessor;
import com.articulate.sigma.KB;
import com.articulate.sigma.parsing.Expr;
import com.articulate.sigma.parsing.ExprToTPTP;
import java.lang.reflect.Method;

public class RuntimeTypeGuardRegression {
    public static void main(String[] args) throws Exception {
        Method method = FormulaPreprocessor.class.getDeclaredMethod(
            "buildTypeGuardExpr", String.class, String.class, KB.class);
        method.setAccessible(true);
        for (String type : new String[]{"(ExtensionFn Oval)", "(ExtensionFn Oval)+", "Human"}) {
            Expr.SExpr guard = (Expr.SExpr) method.invoke(new FormulaPreprocessor(), "?X", type, null);
            Expr term = guard.args().get(1);
            if (type.startsWith("(") && !(term instanceof Expr.SExpr)) {
                throw new AssertionError("Compound class was flattened into an Atom: " + term);
            }
            if (type.equals("Human") && !(term instanceof Expr.Atom)) {
                throw new AssertionError("Atomic class changed structure");
            }
            String translated = ExprToTPTP.translate(guard, false, "fof");
            if (translated.contains("s__(")) {
                throw new AssertionError("Invalid TPTP atom: " + translated);
            }
            System.out.println(type + " -> " + translated);
        }
        System.out.println("PASS: compound instance/subclass guards and atomic control");
    }
}
