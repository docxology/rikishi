import Mathlib.Data.Set.Basic

namespace RikishiEventTransport

theorem pullback_union {α β : Type*} (f : α → β) (A B : Set β) :
    f ⁻¹' (A ∪ B) = (f ⁻¹' A) ∪ (f ⁻¹' B) := rfl

theorem pullback_intersection {α β : Type*} (f : α → β) (A B : Set β) :
    f ⁻¹' (A ∩ B) = (f ⁻¹' A) ∩ (f ⁻¹' B) := rfl

theorem pullback_complement {α β : Type*} (f : α → β) (A : Set β) :
    f ⁻¹' Aᶜ = (f ⁻¹' A)ᶜ := rfl

def collapse (_ : Bool) : Unit := ()

theorem collapse_intersection_failure :
    collapse '' (({false} : Set Bool) ∩ {true}) ≠
      (collapse '' ({false} : Set Bool)) ∩ (collapse '' ({true} : Set Bool)) := by
  intro h
  have member : () ∈ (collapse '' ({false} : Set Bool)) ∩
      (collapse '' ({true} : Set Bool)) :=
    ⟨⟨false, rfl, rfl⟩, ⟨true, rfl, rfl⟩⟩
  rw [← h] at member
  rcases member with ⟨b, ⟨hf, ht⟩, _⟩
  have hfalse : b = false := hf
  have htrue : b = true := ht
  have impossible : false = true := hfalse.symm.trans htrue
  cases impossible

#print axioms pullback_union
#print axioms pullback_intersection
#print axioms pullback_complement
#print axioms collapse_intersection_failure
end RikishiEventTransport
