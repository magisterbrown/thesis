Below, is the list of comments from my first pass:

 

//- There is no methodology or experimental-setup chapter. Setup details are scattered, incomplete, and contradictory.

 

- Chapter 4 is about 3.5 pages, Chapter 5 about 9. The top-ranked parameter gets the least analysis.

 

//- "Cost Models for Parameter Selection" contrasts with 1.3, which says "parameters are not chosen automatically". The research questions also never mention models, yet models are the central contributions.

 

//- Formatting and structural issues:
//
//  - The cover hyphenates the title as "Perfor-mance Evalu-ation".
//
//  - The appendix is not needed -> Experimental setup and charts are part of the work.
//
//  - Fig. 5.1 is actually a table.
//
//  - 5.1.1 repeats 2.1.3.

 

// - 11 references is too few for an MSc thesis. Uncited but used: fANOVA, Gaussian-process Bayesian optimisation, Intel's counter documentation (SDM), the OpenMP specification, the FINUFFT version or commit, and perf itself.

 

 

//Chapter 1:
//
//- The motivation overstates the problem. 1.1 cites an order-of-magnitude spread in runtimes and "several times slower… a few keystrokes away". But Chapter 3 finds that the spread comes almost entirely from turning sorting off, the easiest parameter to reason about. The defaults are within 5.2% of the best configuration found. The text says the opposite ("the ones a user is least equipped to reason about").
//
//- What do you mean by "in a configuration several times slower than one a few keystrokes away".

//- 1.3 is really methodology. It covers the perf profiler, counters and model philosophy, which belongs in a setup chapter. Research questions normally come before the approach, not after.

// - The σ contribution isn't supported. It claims "the optimum generally lies inside [1.25, 2.00], where the library's two-valued heuristic cannot reach it". Chapter 4 never combines the spreading and FFT costs or measures a total-cost optimum. Chapter 3's best configuration used σ = 1.25, which is the default and an endpoint.

 

 

//Chapter 2: Background
//
//- Related work is thin. Obvious omissions include:
//
//  - FFTW's measure-based planning (Frigo & Johnson), the closest analogue to measurement-driven tuning;
//
//  - NFFT3 (Keiner, Kunis & Potts);
//
//  - cuFINUFFT (Shih et al.), which reuses bin sorting and subproblems on GPUs;
//
//  - Barnett's analysis of the ES kernel's aliasing error;
//
//  - the Roofline model;
//
//  - general autotuning frameworks such as OpenTuner.

//- The FFT backend description is inconsistent and partly wrong:
//
//  - 2.2.2 says DUCC is used throughout, but 3.3 and 3.4 talk about FFTW. What is the difference?
//
//  - 4.5.1 calls DUCC a "mixed-radix Cooley–Tukey" FFT, while 2.2.2 describes it as derived from FFTPACK.
//
//  - Are you sure about "prime length costs O(N2)" for pocketfft and DUCC?
//
//- Type 3 gets about a page, then is never analysed. maybe a paragrah is enough?

 

 

//Chapter 3: Exploring Parameter Importance
//
//- 3.1 says "we vary each parameter independently while holding others fixed", but 3.4 and 6.1 say "joint Gaussian-process search".

//- Numbers don't match. The text gives best 0.4825 s and default 0.5087 s; Fig. 3.2 shows 0.474 s and 0.509 s.

//- Is spread_max_sp_size the same as Smax?

//- The 5.2% gain isn't attributed. How did you calculate that? What are the two numbers that resulted in 5.2% gain? The atomic threshold has the same value in both columns of Table 3.1, and that table reports it as "atomic update" instead of the actual threshold number.

- How did you find 5793? 5793×5793=33,558,849 But M=33,554,432.

//- The default Smax contradicts Chapter 5. Table 3.1 lists 10^5 for this type-1 transform, while 5.3.1 says type-1 transforms use 10^4. Check the source.

//- "Not a sensitive knob"?? is contradicted by Chapter 5. 5.3 uses the same workload (2D, 1 GiB, unit density, 64 threads) and shows a 1.8× penalty on spreading wall time across the Smax range.

//- 3.5 makes an unsupported claim. It says the heuristic "can select a fine-grid size whose FFT costs twenty times what a neighbouring choice would", "as shown above". Nothing above shows this.

 

 

//Chapter 4: Analysis of the Upsampling Factor

//- The chapter's goal isn't reached. It sets out to show "how to select σ optimally", but spreading and FFT are validated separately and never combined. There is no total-cost curve, predicted optimum, measured optimum, or comparison with the heuristic, so none of the gains over the heuristic are quantified.

//- Eq. 4.1 has no source.

//- The FFT validation (Fig. 4.2) has problems:

//  - The caption says "1 and 16 threads", the legend says "all thr", and the machine has 20 cores / 40 threads.

  - It plots throughput against N but never tests how cost depends on σ.

//  - The sentence in 4.5.1 is unclear ("performs only O(log Ñ) pralelized over multiple threads arithmetic operations, per element").

//- Google Benchmark statement is not correct. It isn't "cycle-accurate", and by default it doesn't report a standard deviation.

//a broken "Appendix ??"- Smaller points: "Analytical Measurements" is an odd title for an experimental section, and 4.5.2 contains a broken "Appendix ??".

 

 

//Chapter 5: Analysis of the Spreader Parameters (strongest chapter)

//- The hardware doesn't match. Chapters 3 and 5 use 64 threads, and Table 5.1's ratios imply a 48 KiB L1d and a 1.25 MiB L2. That is consistent with an Ice Lake-SP-class part, not the documented Xeon E5-2698 v4, which has 40 threads and a 32 KiB L1d. NUMA and thread pinning are never discussed, and they matter for the memory-contention arguments.

//- Figs. 5.6 and 5.7 contradict the method. They plot gathering and adding in milliseconds, but 1.3 says these steps can't be timed with a clock. The conversion needs explaining.

- The spreading working set omits padding. The text gives 16·bx·by bytes, but Table 5.1b's ratios look weird. Do they match 16·bx·by?

- Load imbalance is asserted, not shown. Per-thread busy time would settle it.

- 5.3.1 is mislabelled. It's titled "Older heuristics" but describes the current heuristic, and its claims about scheduling overhead and cache spill have no evidence.

 

 

Chapter 6: Conclusion

- The research questions aren't answered explicitly, one by one.

- It overstates. "Essentially all of the work" contradicts Chapter 3's 10–20% share for setpts. It says closed-form models were given for both σ costs, but Chapter 4 showed the FFT model isn't predictive. The Smax trade-off is described differently than in Chapter 5 ("write traffic vs load imbalance" instead of gathering vs adding).

- Limitations are incomplete. It says "a single class of machine". What do you mean by "Finally, the sort bin dimensions, are not exposed by the library at all, and external interface had to be altered to modify them"? Why you didn't include that in the work?

 

 

Regards,
