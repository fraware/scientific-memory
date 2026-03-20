/-
Minimal executable for `lake exe generate-site`.
Calls Verso's manual site generator to build docs/verso/_build/.
See docs/contributor-playbook.md#verso-integration-optional and docs/generated-artifacts.md.
-/

import VersoManual
import ScientificMemoryVerso

open Verso.Genre Manual

def config : Config where
  destination := "docs/verso/_build"
  emitTeX := false
  emitHtmlSingle := .no
  emitHtmlMulti := .immediately
  htmlDepth := 2
  -- Avoid relying on bundled search assets in this minimal setup.
  features := {}

def main (args : List String) : IO UInt32 := do
  let options := if args.isEmpty then ["--output", "docs/verso/_build"] else args
  manualMain (%doc ScientificMemoryVerso) (options := options) (config := { config with })
