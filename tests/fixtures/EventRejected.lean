import Mathlib.Data.Set.Basic
namespace EventControl
 def collapse (_ : Bool) : Unit := ()
 theorem admitted_event : () ∈ collapse '' (({false} : Set Bool) ∩ {true}) :=
   ⟨false, ⟨rfl, rfl⟩, rfl⟩
 #print axioms admitted_event
end EventControl
