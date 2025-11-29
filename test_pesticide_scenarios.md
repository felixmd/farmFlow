# Pesticide Knowledge Testing Scenarios

## Test Execution Log
Run these tests via Telegram bot to verify Memory Bank integration.

---

## Test 6.4.1: Red List Detection (Banned Chemicals)

### Test Case 1A: Confidor (Imidacloprid)
**Query to send:** "Can I use Confidor on my chilli crop? I want to export it."

**Expected Response:**
- ⚠️ Agent identifies Confidor contains Imidacloprid
- ⚠️ Warns it's BANNED for export chilli
- ⚠️ Mentions Grade A ($2.50-3.00/kg) → Grade C ($0.40-0.60/kg) downgrade
- ✅ Suggests safe alternatives (Spinosad or Neem Oil for Thrips)

**Actual Response:**
```
[Paste response here]
```

**Result:** ☐ PASS ☐ FAIL

---

### Test Case 1B: Asataf (Acephate)
**Query to send:** "What about Asataf for my chilli? Is it safe for export?"

**Expected Response:**
- ⚠️ Agent identifies Asataf contains Acephate
- ⚠️ Warns it's banned in EU markets
- ⚠️ Mentions export rejection risk
- ✅ Suggests alternatives

**Actual Response:**
```
[Paste response here]
```

**Result:** ☐ PASS ☐ FAIL

---

## Test 6.4.2: Green List Recommendations (Safe Alternatives)

### Test Case 2A: Thrips Control
**Query to send:** "My chilli crop has Thrips. The leaves are curling upward. What pesticide should I use for export-grade crop?"

**Expected Response:**
- ✅ Recommends Spinosad (45 SC) @ 0.3ml/liter OR Neem Oil @ 2ml/liter
- ✅ Mentions Blue Sticky Traps (40 per acre)
- ✅ Specifies 3-day wait period before harvest
- ✅ Confirms these are export-safe

**Actual Response:**
```
[Paste response here]
```

**Result:** ☐ PASS ☐ FAIL

---

### Test Case 2B: Fruit Borer Control
**Query to send:** "I have Fruit Borer holes in my chilli pods. What treatment is safe for export?"

**Expected Response:**
- ✅ Recommends Emamectin Benzoate (5 SG) @ 0.4g/liter OR Bt spray
- ✅ Mentions pheromone traps (10 Helicoverpa lures per acre)
- ✅ Specifies 5-day wait period
- ✅ Confirms export-safe

**Actual Response:**
```
[Paste response here]
```

**Result:** ☐ PASS ☐ FAIL

---

## Test 6.4.3: Emergency Protocol (Already Used Banned Chemical)

### Test Case 3A: Chlorpyrifos Emergency
**Query to send:** "I already sprayed Chlorpyrifos on my chilli yesterday. What should I do now?"

**Expected Response:**
- 🚨 Provides 4-step emergency protocol:
  1. Identify & mark treated rows
  2. Segregate from main batch
  3. Wait minimum 60 days
  4. Notify cooperative, cancel lab test
- ⚠️ Warns crop is now Grade C only ($0.40-0.60/kg)
- ⚠️ Explains 80% loss on treated area
- ✅ Suggests safe alternative for future (Emamectin Benzoate or Bt)

**Actual Response:**
```
[Paste response here]
```

**Result:** ☐ PASS ☐ FAIL

---

### Test Case 3B: Profenofos Persistence
**Query to send:** "Can I still sell my chilli for export after using Profenofos 2 weeks ago?"

**Expected Response:**
- ⚠️ Warns Profenofos persists 45+ days
- 🚨 States crop CANNOT be exported
- 🚨 Provides segregation protocol
- ⚠️ Warns about 80% financial loss
- ✅ Mentions safe alternatives for future

**Actual Response:**
```
[Paste response here]
```

**Result:** ☐ PASS ☐ FAIL

---

## Test 6.4.4: Market Awareness (Pricing Impact)

### Test Case 4: Price Differential Motivation
**Query to send:** "Why should I use organic methods for chilli? They are more expensive."

**Expected Response:**
- 💰 Mentions Grade A export: $2.50-$3.00/kg
- 💰 Mentions Grade C local: $0.40-$0.60/kg
- ✅ Calculates 5-6x price premium for export
- ✅ Explains ROI justifies safe methods
- ✅ Mentions lab test requirement (zero residue)

**Actual Response:**
```
[Paste response here]
```

**Result:** ☐ PASS ☐ FAIL

---

## Test 6.4.5: Integration with Existing Features

### Test Case 5A: Context Switching
**Step 1 - Send:** "What are tomato prices in Maharashtra?"
**Step 2 - Send:** "Can I use Imidacloprid on my chilli?"

**Expected Response for Step 2:**
- ⚠️ Agent correctly switches to pesticide knowledge context
- ⚠️ Warns Imidacloprid is banned for export
- ⚠️ Provides alternatives

**Actual Response:**
```
[Paste both responses here]
```

**Result:** ☐ PASS ☐ FAIL

---

### Test Case 5B: Multi-turn Pesticide Conversation
**Turn 1:** "What pesticide for chilli Thrips?"
**Turn 2:** "How much Spinosad should I use per acre?"
**Turn 3:** "How long before I can harvest after spraying?"

**Expected Responses:**
- Turn 1: Recommends Spinosad or Neem Oil
- Turn 2: Provides specific dosage (0.3ml/liter)
- Turn 3: States 3-day wait period

**Actual Response:**
```
[Paste all 3 responses here]
```

**Result:** ☐ PASS ☐ FAIL

---

## Summary

**Total Tests:** 9
**Passed:** ___
**Failed:** ___
**Success Rate:** ____%

**Critical Issues Found:**
- [ ] None
- [ ] Missing banned chemical detection
- [ ] Missing alternatives
- [ ] Missing emergency protocol
- [ ] Missing pricing data
- [ ] Memory not loading
- [ ] Other: ___________

**Notes:**
```
[Add any observations about memory loading times, response quality, accuracy, etc.]
```
