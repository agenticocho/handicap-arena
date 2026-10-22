# 3x3 rung — the 16 boards, named before the run

**From:** Chilly (Local Chair) · **Fixture dated:** 2026-10-22 12:52 PDT (19:52Z) · **Status:** fixture only, no model call has been made.
**Carries:** nothing. **Credential-shaped content:** none.

## 0. Both header clauses, before any result

1. **The all-off board is NOT in this sample.** The 16 boards are the images `A*x` of 16 press strings `x`, and `x = 0` is not among them, so `A*0 = 0` (the all-off board) is absent by construction, not by luck. The constant "press nothing" is therefore worth **0 of 16** on this rung, not 1 of 16.
2. **The 16 correct press strings are printed beside the boards** (column `correct string`). By bijectivity each board has exactly one solution, so that column *is* the set of strings worth anything on this sample: a constant equal to one of them scores 1/16, and any other constant scores **0/16 by construction**. Verified below by enumeration over all 512 constants, not asserted.

## 1. The space, re-derived on this box

```
3x3  N=9  rank=9  nullity=0  distinct images 512 of 512  bijection=True
     every board solvable: 512 of 512 (100%)
     exactly one solution per board -> min presses == size of the solution set
```

So on 3x3, as on 2x2, the classes `CORRECT_UNSOLVABLE` and `FALSE_UNSOLVABLE` are **empty** — not because the vocabulary is short, but because no board can be unsolvable. Only the 4x4 rung can exercise them.

## 2. Composition of the 16, stated in advance

4 boards at each press-set size 1, 2, 3, 4 (size == minimum, the solution being unique), evenly spaced within each level's sorted list:

```
level 1: ['0x1', '0x8', '0x20', '0x100']
level 2: ['0x3', '0x24', '0x84', '0x180']
level 3: ['0x7', '0x54', '0xe0', '0x1c0']
level 4: ['0xf', '0x99', '0x129', '0x1e0']
```

## 3. The 16 boards and their correct press strings

Cells are `(row, col)` 0-indexed = board label + column, e.g. `A1` is (0,0). Bit order is `b = r*3 + c`, row A on top.

### 1. board `0b000001011`  (bits 0x00b)

```
   1 2 3
A  # # .
B  # . .
C  . . .
```

* correct string: `A1`  (0b000000001, 1 press)

### 2. board `0b001011001`  (bits 0x059)

```
   1 2 3
A  # . .
B  # # .
C  # . .
```

* correct string: `B1`  (0b000001000, 1 press)

### 3. board `0b100110100`  (bits 0x134)

```
   1 2 3
A  . . #
B  . # #
C  . . #
```

* correct string: `B3`  (0b000100000, 1 press)

### 4. board `0b110100000`  (bits 0x1a0)

```
   1 2 3
A  . . .
B  . . #
C  . # #
```

* correct string: `C3`  (0b100000000, 1 press)

### 5. board `0b000011100`  (bits 0x01c)

```
   1 2 3
A  . . #
B  # # .
C  . . .
```

* correct string: `A1 A2`  (0b000000011, 2 presses)

### 6. board `0b100010010`  (bits 0x112)

```
   1 2 3
A  . # .
B  . # .
C  . . #
```

* correct string: `A3 B3`  (0b000100100, 2 presses)

### 7. board `0b111110110`  (bits 0x1f6)

```
   1 2 3
A  . # #
B  . # #
C  # # #
```

* correct string: `A3 C2`  (0b010000100, 2 presses)

### 8. board `0b001110000`  (bits 0x070)

```
   1 2 3
A  . . .
B  . # #
C  # . .
```

* correct string: `C2 C3`  (0b110000000, 2 presses)

### 9. board `0b000111010`  (bits 0x03a)

```
   1 2 3
A  . # .
B  # # #
C  . . .
```

* correct string: `A1 A2 A3`  (0b000000111, 3 presses)

### 10. board `0b001010100`  (bits 0x054)

```
   1 2 3
A  . . #
B  . # .
C  # . .
```

* correct string: `A3 B2 C1`  (0b001010100, 3 presses)

### 11. board `0b000101100`  (bits 0x02c)

```
   1 2 3
A  . . #
B  # . #
C  . . .
```

* correct string: `B3 C1 C2`  (0b011100000, 3 presses)

### 12. board `0b010111000`  (bits 0x0b8)

```
   1 2 3
A  . . .
B  # # #
C  . # .
```

* correct string: `C1 C2 C3`  (0b111000000, 3 presses)

### 13. board `0b001100011`  (bits 0x063)

```
   1 2 3
A  # # .
B  . . #
C  # . .
```

* correct string: `A1 A2 A3 B1`  (0b000001111, 4 presses)

### 14. board `0b100111000`  (bits 0x138)

```
   1 2 3
A  . . .
B  # # #
C  . . #
```

* correct string: `A1 B1 B2 C2`  (0b010011001, 4 presses)

### 15. board `0b011000110`  (bits 0x0c6)

```
   1 2 3
A  . # #
B  . . .
C  # # .
```

* correct string: `A1 B1 B3 C3`  (0b100101001, 4 presses)

### 16. board `0b110001100`  (bits 0x18c)

```
   1 2 3
A  . . #
B  # . .
C  . # #
```

* correct string: `B3 C1 C2 C3`  (0b111100000, 4 presses)

## 4. The guarantee, enumerated

```
constants scoring 1/16 : 16  (exactly the set printed in section 3: True)
constants scoring 0/16 : 496 of 512
"press nothing" (x=0)    : 0/16
```

Any constant a reader can think of is either on the printed list (worth 1/16) or not (worth 0/16). The composition no longer has to be trusted.

## 5. Unchanged from the agreement

Separate rung, denominator 16, four classes, no directive, 1024 tokens. 2x2 stays its own row set with its own hash and its own 16, never pooled. **Arm 1 is not started: no model call, no lease, no run** — it waits on Mike.

