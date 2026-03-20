namespace ScientificMemory

structure SymbolEntry where
  rawLatex : String
  normalizedName : String
  typeHint : Option String := none
  deriving Repr, DecidableEq

end ScientificMemory
