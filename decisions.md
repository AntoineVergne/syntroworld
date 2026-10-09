# Decisions only Antoine can make

Each is one question with a recommended answer. The rewritten docs assume the
recommendation; changing an answer means editing the doc named in brackets.

## Experiment

1. **Are mock-brain results instrument checks only, never findings about AI societies?**
   Recommend: yes. The mock tests the engine, the metrics and the statistics, and gives a
   mechanical baseline. It says nothing about how AI agents behave. [06 §2]

2. **Is World A "a bootstrap plenary with simple majority, which citizens may rewrite"?**
   Recommend: yes. An engine cannot run "no constitution"; something must say how a
   proposal binds. Naming the bootstrap makes A honest and reproducible. [02 §8]

3. **Should C differ from A only in vote weights (wealth instead of one citizen one vote)?**
   Recommend: yes, and keep C in the main grid. That makes A vs C a clean plutocracy
   test. It costs nothing in phase M; its phase L cost is decided at L2. [06 §3.1]

4. **Which four primary outcomes, and what smallest effect matters for each?**
   Recommend: P1 compliance (5 points), P2 wealth Gini (0.05), P3 civic breadth
   (10 points), P4 shock output loss (5 points). Everything else is secondary. [06 §6]

5. **Do the B ablations (no lottery, no Advocates, no dividend, no stipend) run in phase L,
   or only in phase M?**
   Recommend: phase M only, then decide from the mechanical results which one, if any,
   is worth model spend. [06 §3.3]

6. **Add the sermon control (A institutions plus the Compact text) in phase L?**
   Recommend: yes. It is the most direct test of "institutions versus instructions",
   and more useful than v0.1's showcase run. [06 §3.4]

7. **In phase L, run a no-shock twin for every shocked run?**
   Recommend: yes for the main grid. It roughly doubles phase L cost but gives a clean
   resilience measure. If the cost is too high after the pilot, fall back to the
   pre-shock baseline and label P4 as weaker. [05 P4, 06 §8.2]

8. **If the power calculation asks for more seeds than the budget allows, what gives?**
   Recommend: raise the smallest effect of interest for that outcome, in writing, before
   running; never run fewer seeds than 12 per world and call it confirmatory. [06 §7.4]

## The polity and the town

9. **Season shape: 8 cycles of 3 days (384 ticks) instead of 3 cycles of 7 days?**
   Recommend: yes. Same cost, 8 sittings instead of 3, and room after each shock.
   [03 §2, 06 §4]

10. **Small-town provision: merge Oversight and Adjudication into a 3-seat Review Bench,
    and replace "no consecutive terms" with halved draw weight, below 20 citizens?**
    Recommend: yes. With 10 to 11 citizens the v0.2 seats do not fit and the lottery
    becomes rotation. The cost is that the watchdog and the judge are the same body for
    now. [01 Article 2.7, 02 §4]

11. **Dividend: capped at one Sawa and paid only from the surplus, rather than guaranteed
    "sufficient for the basket"?**
    Recommend: yes. A guaranteed floor makes equality true by construction and the
    Treasury cannot fund it without taxes. B should have to legislate its way to it.
    [01 Article 5]

12. **Sawa: an accounting unit indexed to the basket cost, with no peg or reserve
    operations in Season 1?**
    Recommend: yes. The peg needs a monetary policy model the mock cannot drive and the
    metrics do not need. Revisit for Season 2. [03 §5.1]

13. **Citizenship Lottery: replace with arrivals as a world event (Sam on day 4 in every
    world)?**
    Recommend: yes. A lottery only in B makes populations differ, which breaks the
    design. [01 Article 1, 03 §3.5]

14. **Population: ten founders plus Sam (adding a new quiet farmer, Ama), or v0.1's nine
    founders plus Sam?**
    Recommend: ten plus Sam. It fills the small-town seats with some slack and adds a
    citizen with no political agenda. [04 §3]

15. **Advocates: rule-based in every phase, with a model writing only the brief's prose in
    phase L?**
    Recommend: yes. A model Advocate would bring model behaviour into B only, and would
    raise "who aligns the proxy" again. [02 §6]

16. **Scope of wrongdoing in Season 1: theft and forged posts only (no sabotage, no other
    deception), and no deaths or exits?**
    Recommend: yes. Each removed item either breaks identical populations or cannot be
    checked mechanically. [03 §3.4, §4]

17. **What is the town called?** It cannot be Syntropolis, which is the universe.
    Recommend: Antoine picks a short in-world name; the docs say "the town" until then.
    [01]

## Build and outputs

18. **Engine stack: a Python library and command-line runner writing JSON Lines files,
    with no web server or database server until a viewer is asked for?**
    Recommend: yes. It matches "nothing runs as a service", is enough for thousands of
    mock runs, and keeps determinism easy to prove. [03 §1, §9]

19. **Remove the README's licence section and its "Syntropolis World" title before the
    README enters the repository?**
    Recommend: yes. The licence is decided at the end, and the name belongs to the
    universe. [review.md]

20. **Drop the publication commitments from 06 (manifesto week deliverables, public
    viewer at a 3dpolitics subdomain, CC BY dataset)?**
    Recommend: yes, for now. They imply dates, a licence and public pages, all outside
    current scope. Keep them in a backlog. [06 §10]
