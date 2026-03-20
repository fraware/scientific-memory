namespace ScientificMemory

inductive AssumptionKind where
  | physicalRegime
  | domainRestriction
  | smoothness
  | boundedness
  | measurementAssumption
  | unitConvention
  | approximation
  | editorial
  | other
  deriving Repr, DecidableEq

end ScientificMemory
