namespace ScientificMemory

abbrev UnitSymbol := String

structure UnitInfo where
  symbol : UnitSymbol
  dimension : String
  deriving Repr, DecidableEq

end ScientificMemory
