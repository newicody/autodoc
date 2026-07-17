# Projects bundle transient filter

```text
managed root scan
      |
      +-- known destination ----------> managed comparison
      |
      +-- __pycache__ / .pyc / .pyo --> ignored_transient_files
      |
      +-- every other extra ----------> unknown_extra_files
                                             |
                                             v
                                      operator review
```

The filter changes reporting only. It performs no deletion, ignores no source
file and broadens no safe-delete boundary.
