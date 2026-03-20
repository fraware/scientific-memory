namespace ScientificMemory

inductive VerificationBoundary where
  | fullyMachineChecked
  | machineCheckedPlusAxioms
  | numericallyWitnessed
  | schemaValidOnly
  | humanReviewOnly
  deriving Repr, DecidableEq

end ScientificMemory
