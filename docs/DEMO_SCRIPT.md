# Demo script, slides and video

## A. 3-slide deck (`docs/slides.pdf`, made in Claude Slides or Canva and exported)

**Slide 1: The problem**
- Title: *"Picking the best 3 of 6 stocks, on a quantum computer"*
- Visual: the risk/return frontier figure with all C(6,3) = 20 baskets as dots and the optimal basket highlighted
- Subtitle: robo-advisor model baskets · NSE large caps · return ↑ risk ↓

**Slide 2: The idea and the result**
- Left: two circuit cartoons, "Penalty QAOA: searches 64 strings, 44 invalid" vs "XY-QAOA: Dicke state + XY mixer, only the 20 valid baskets"
- Right: `headline.png` (P(optimal) bars + random line)
- Callout: *"~7× better than chance · 100% valid · penalty-QAOA = chance"*

**Slide 3: Real hardware and honesty**
- `noise_ladder.png` (ideal → noisy → post-selected → mitigated → ibm_⟨backend⟩)
- Three bullets: "symmetry post-selection = free error detection" · "classical brute force is still faster at this size" · "next: more constraints as circuit symmetries"
- QR codes: repo + live app

## B. 2-minute video script (screen recording + voice; ~260 words)

| Time | Screen | Say |
|---|---|---|
| 0:00–0:15 | Slide 1 | "Robo-advisors sell model baskets: pick k stocks out of n so return goes up and risk goes down. The number of choices explodes combinatorially. I built this with Qiskit." |
| 0:15–0:40 | Notebook: QUBO cell + penalty results | "The textbook approach turns 'exactly k stocks' into a penalty. I tested that carefully, with three penalty strengths and also CVaR. It finds the best basket no more often than random guessing." |
| 0:40–1:05 | Circuit diagram (Dicke + XY mixer) | "So I moved the constraint into the circuit. A Dicke state starts in an equal mix of only valid baskets, and an XY mixer swaps stocks in and out without ever changing the count. Every shot is a valid portfolio." |
| 1:05–1:25 | `headline.png` + benchmark table | "Result: the optimal basket comes up about 7 times more often than chance, and it's the top answer, tested on 20 instances against brute force and simulated annealing." |
| 1:25–1:45 | IBM dashboard job page → `noise_ladder.png` | "On a real IBM quantum computer, noise lets some invalid baskets through. Since the ideal circuit can't produce them, I can discard them. That's free error detection, and it brings us back towards the ideal." |
| 1:45–2:00 | Slide 3 | "Honest limits: at this size a laptop solves it instantly, so there's no quantum advantage claimed. But building constraints into the circuit is what makes quantum optimisation work at all. Code, report and live demo are linked." |

Record with OBS or the Windows/Mac screen recorder at 1080p. Upload to YouTube as **Unlisted**. Put the link in the README and the brief.

## C. 3-minute live demo (if you reach the top 3, Day 3 13:00)
1. (20 s) The pitch sentence from `09_RUBRIC_MAP.md`.
2. (60 s) Live app: choose 6 tickers, k = 3, q = 0.5 → run → show that QAOA's top basket = brute force. Change q to 1.0 and the basket shifts to defensive stocks. *The business story in one click.*
3. (40 s) "Why XY beats penalty" tab.
4. (40 s) Hardware tab: job ID, noise ladder.
5. (20 s) Limits + thank you.
Have the app **already open and warmed up** (cache filled), plus a backup: the Pages report and a local `streamlit run`.
