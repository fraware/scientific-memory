namespace ScientificMemory

structure SourcePosition where
  page : Nat
  offset : Nat
  deriving Repr, DecidableEq

structure SourceSpan where
  sourceFile : String
  startPos : SourcePosition
  endPos : SourcePosition
  deriving Repr, DecidableEq

structure Provenance where
  paperId : String
  claimId : String
  sourceSpan : SourceSpan
  reviewerNote : Option String := none
  deriving Repr, DecidableEq

end ScientificMemory
