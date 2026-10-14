---
title: "Online Appendix — Votes Without Neighborhoods"
---

This appendix gives the formal framework and proofs (A), the data (B), the results cited in the text (C) and the re-implementation of a published allocation (D). Further tables, and the code that produces every number, are in the replication files.

# A. Formal framework, proofs and computation

**Parameters and symbols.** $\eta$: uniform movement cap (share of a station's ballots cast by non-residents beyond the movement the roll forces); $\lambda$: multiple of the mobility-calibrated cap; $\delta$: tolerance for residents' out-of-zone composition around their station; $s$: tolerance for residents' early composition beyond their station's own departure from the benchmark $a^F$; $t$: tolerance for movers' composition around their home station; $\kappa$: bound on the within-jurisdiction slope of residents' early-vote departures on log price (Section 4.5). $s^*$, $\lambda^*$, $\eta^*$, $\delta^*$, $\kappa^*$: the largest value of each parameter at which the lower bound of a slope stays positive. $z$: roll-based share; $y$: valid-vote share. Columns A–F: the assumption sets of Table 2.

## A.1 Observables, unknowns and the polytope

Consider one counting jurisdiction $g$: a district (gu), or a National Assembly constituency in 2024 (48 units). It contains neighborhoods (dongs) $i$ and in-zone early stations $j$, one per dong. Ballot categories $c$ are candidates and invalid ballots. The returns and the roll give, for each dong, election-day ballots $A_{ic}$ (cast by residents of $i$), in-zone early ballots $K_{jc}$ counted at station $j$, the certified electorate $E_i$ and the electorate remaining on the election-day roll $D_i$, which is printed after early voting with early voters marked and excludes residents registered for at-home, shipboard or overseas voting. $E_i-D_i$ is the number of residents removed from the election-day roll. Jurisdiction totals are the out-of-zone early ballots $P_c$, the at-home, shipboard and overseas ballots $Q_c$, and $U=\sum_i(E_i-D_i)-\sum_jK_j-\sum_cP_c-\sum_cQ_c$, the removed residents who cast no counted ballot. Write $A_i=\sum_cA_{ic}$, $K_j=\sum_cK_{jc}$, $H_i=A_i+E_i-D_i$ and $r_j=\max\{0,K_j-(E_j-D_j)\}$.

The unknowns are $F_{ijc}$ (in-zone early ballots of residents of $i$ cast at $j$), $P_{ic}$ and $Q_{ic}$ (residents' pooled ballots) and $U_i$ (removed residents who did not vote), all non-negative and subject to
$$\textstyle\sum_{j,c}F_{ijc}+\sum_cP_{ic}+\sum_cQ_{ic}+U_i=E_i-D_i,\tag{R}$$
$$\textstyle\sum_iF_{ijc}=K_{jc};\quad \sum_iP_{ic}=P_c;\quad \sum_iQ_{ic}=Q_c;\quad \sum_iU_i=U,\tag{S}$$
$$F_{ijc}=0\ \text{ if $i$ and $j$ lie in different early-voting zones.}\tag{Z}$$
Residents' count of category $c$ is $N_{ic}=A_{ic}+\sum_jF_{ijc}+P_{ic}+Q_{ic}$. The roll-based share is $z_{ic}=N_{ic}/H_i$ and the valid-vote share $y_{ic}=N_{ic}/(H_i-U_i-N_{i,\mathrm{inv}})$.

**Restrictions.** (M$_\eta$) caps non-resident ballots at station $j$ at $r_j+\eta K_j$; the mobility-calibrated scenario caps them at $r^\rho_j+\lambda C_j$, with $r^\rho_j=\max\{r_j,K_j-\phi_u(E_j-D_j)\}$, $\phi_u$ the zone's ratio of in-zone early ballots to removed residents, and $C_j$ the calibrated cross-dong flow (B.4). (A$_\delta$) bounds residents' out-of-zone composition around an anchor $\tilde a_{ic}$: $(\tilde a_{ic}-\delta)P_{i\cdot}\le P_{ic}\le(\tilde a_{ic}+\delta)P_{i\cdot}$, with $\tilde a_{ic}=K_{ic}/K_i$ (the station's composition; in 2012, without in-zone early voting, the election-day composition), or the station composition shifted by the jurisdiction's out-of-zone minus in-zone early composition, optionally plus its price relation. (A$^F_s$) bounds residents' in-zone early composition around $a^F_{ic}=\operatorname{clip}_{[0,1]}(A_{ic}/A_i+\gamma^K_{gc})$, with $\gamma^K_{gc}$ the jurisdiction's in-zone early minus election-day composition:
$$(a^F_{ic}-\omega_{ic})\textstyle\sum_{j,c'}F_{ijc'}\le\sum_jF_{ijc}\le(a^F_{ic}+\omega_{ic})\sum_{j,c'}F_{ijc'},\qquad\omega_{ic}=|K_{ic}/K_i-a^F_{ic}|+s,$$
with the lower limit truncated at zero. (A$^{mv}_t$) bounds movers: with $k_{ic}=K_{ic}/K_i$, $(k_{ic}-t)\sum_{j\ne i,c'}F_{ijc'}\le\sum_{j\ne i}F_{ijc}\le(k_{ic}+t)\sum_{j\ne i,c'}F_{ijc'}$. (A$^\kappa$) bounds the alignment of residents' early-vote departures with price. Let $\Delta_i=\sum_jF_{ij,\mathrm{cons}}-a^F_{i,\mathrm{cons}}\sum_{j,c}F_{ijc}+P_{i,\mathrm{cons}}-\tilde a_{i,\mathrm{cons}}P_{i\cdot}$, let $I_u$ be the dongs of counting jurisdiction $u$ with a price (in 2024 a constituency, not a gu), $\overline{x}_u$ their mean log price, and $v_i=(x_i-\overline{x}_u)/\sum_{j\in I_u}(x_j-\overline{x}_u)^2$ for $i\in I_u$ and $0$ otherwise, so that $\sum_{i\in u}v_i=0$. Then $|\sum_{i\in u}v_i\Delta_i/H_i|\le\kappa$ for every $u$: the within-jurisdiction OLS slope of departures, as shares of the roll, on log price. (A$^\kappa_P$) is the same restriction on out-of-zone departures alone, $\Delta^P_i=P_{i,\mathrm{cons}}-\tilde a_{i,\mathrm{cons}}P_{i\cdot}$, used in place of (A$_\delta$). The observed reference for $\kappa$ applies the same weights to station departures $(K_{i,\mathrm{cons}}-a^F_{i,\mathrm{cons}}K_i)/H_i$. $\Lambda$ is the set of non-negative unknowns satisfying (R), (S), (Z) and the imposed restrictions.

## A.2 Results

**Lemma 1.** Under (R), (S) and non-negativity, $\sum_{i\ne j}\sum_cF_{ijc}\ge r_j$ for every $j$.

*Proof.* By (S), $\sum_{i\ne j}\sum_cF_{ijc}=K_j-\sum_cF_{jjc}$, and by (R) $\sum_cF_{jjc}\le E_j-D_j$. $\square$

**Corollary 1.** Under (M$_0$), every dong $j$ with $r_j>0$ has $P_{j\cdot}=Q_{j\cdot}=U_j=0$ and $F_{jk\cdot}=0$ for $k\ne j$: its removed residents all voted at their own station.

*Proof.* Non-resident ballots at $j$ are at most $r_j$, so $F_{jj\cdot}\ge K_j-r_j=E_j-D_j$, and (R) forces every other term to zero. $\square$

Summing (R) over the dongs of a zone $u$ and using (S) and (Z) gives a zone-level identity, $\sum_{i\in u}(P_{i\cdot}+Q_{i\cdot}+U_i)=\sum_{i\in u}(E_i-D_i)-\sum_{j\in u}K_j$.

**Proposition 1.** Suppose $\Lambda$ is nonempty. It is a convex polytope. For any weights $w$, the set of values of $\sum_iw_iz_{ic}$ over $\Lambda$ is $[\min_\Lambda,\max_\Lambda]$, each endpoint the value of a linear program.

*Proof.* All constraints are linear in the unknowns, and $z_{ic}$ is linear because $H_i$ is observed; a linear function on a convex polytope attains every value between its extremes. $\square$

The bounds are sharp for the continuous relaxation, relative to the information in (R), (S), (Z) and the restrictions. Jurisdictions share no constraint, so citywide extrema are sums of jurisdiction-specific extrema.

**Proposition 2.** Let $w=w^{\text{btw}}+w^{\text{wth}}$ with $w^{\text{btw}}_i=H_i\mu_{g(i)}$. (i) $\sum_iw^{\text{btw}}_iz_{ic}$ is point-identified by the jurisdiction totals. (ii) The identified set of $\sum_iw_iz_{ic}$ is that number plus the identified set of $\sum_iw^{\text{wth}}_iz_{ic}$. (iii) Without (A$_\delta$), (A$^\kappa$) and (A$^\kappa_P$), if some point of $\Lambda$ has $P_{ic'}>0$ and $P_{i'c}>0$ for dongs $i\ne i'$ and distinct ballot categories $c\ne c'$ in one jurisdiction, the slope is not point-identified whenever $w_i/H_i\ne w_{i'}/H_{i'}$. (iv) The width is at most $\sum_g(\max_{i\in g}w_i/H_i-\min_{i\in g}w_i/H_i)M_{gc}$, with $M_{gc}=P_{gc}+Q_{gc}+\sum_{j\in g}\min\{K_{jc},m_j\}$ and $m_j$ the movement cap.

*Proof.* (i) $\sum_{i\in g}N_{ic}$ equals the observed jurisdiction total. (ii) Linearity in $w$. (iii) Exchanging $\varepsilon$ ballots between $(i,c),(i,c'),(i',c),(i',c')$ leaves every constraint unchanged and moves the slope by $\varepsilon(w_i/H_i-w_{i'}/H_{i'})$. (iv) Between two points of $\Lambda$, $\sum_{i\in g}(N_{ic}-N'_{ic})=0$ and the positive parts are bounded by $M_{gc}$, because both points keep at least $K_{jc}-m_j$ of station $j$'s category-$c$ ballots with its residents; hence $\sum_{i\in g}(w_i/H_i)(N_{ic}-N'_{ic})\le\operatorname{range}_g(w/H)\,M_{gc}$. $\square$

**Lemma 2.** With $\pi_w=\sum_i(x_i-\overline{x}_{g(i)})^2/\sum_i(x_i-\overline{x})^2$, the pooled OLS weights satisfy $w^P=\pi_ww^{FE}+v$, $v_i=(\overline{x}_{g(i)}-\overline{x})/\sum_k(x_k-\overline{x})^2$, so for every $\ell\in\Lambda$, $\theta(w^P;\ell)=\pi_w\theta(w^{FE};\ell)+\theta(v;\ell)$.

*Proof.* Decompose $x_i-\overline{x}$ into within- and between-gu parts and use linearity. $\square$

$\theta(v;\ell)$ is a gradient computed from residence-based dong shares; it is not the gradient of gu totals and depends on the allocation. It distinguishes the between-district component of a dong-level regression from a regression on fully counted district totals.

**Proposition 3.** Holding all other coefficients fixed, $\Lambda$ weakly expands as we increase $\eta$, $\lambda$, $\delta$, $s$ and $t$, and when any restriction, including (Z), is removed; so the lower bound of a $z$ slope is non-increasing in each parameter and breakdown points are well defined.

*Proof.* Each change relaxes inequalities or removes equalities. $\square$

**Proposition 4.** With $T_i=H_i-U_i-N_{i,\mathrm{inv}}$, $y_{ic}-z_{ic}=y_{ic}(U_i+N_{i,\mathrm{inv}})/H_i$, so with dong bounds $\underline y_{ic}\le y_{ic}\le\overline{y}_{ic}$ over $\Lambda$, $w_iy_{ic}\ge w_iz_{ic}+k_i(U_i+N_{i,\mathrm{inv}})/H_i$ with $k_i=w_i\underline y_{ic}$ ($w_i>0$) or $w_i\overline{y}_{ic}$ ($w_i<0$). The right side is linear, so one LP gives a valid lower bound on the valid-vote slope; the upper bound is symmetric.

*Proof.* $N/T-N/H=N(H-T)/(TH)$ and $(U_i+N_{i,\mathrm{inv}})/H_i\ge0$. $\square$

## A.3 Further quantities

*The neighborhood contrast* weights each dong priced above its gu's median by $\nu_g/n^{\text{high}}_g$ and every other dong with a price by $-\nu_g/n^{\text{low}}_g$, with $\nu_g$ proportional to the gu's number of dongs with a price.

*The region of assumptions.* $s^*(\lambda,\delta)=\sup\{s:\min_\Lambda\theta>0\}$, found by bisection on $[s_{\min},0.30]$ (width $0.3/256$), where $s_{\min}$ is the smallest feasible slack; reported values are the lower end of the final interval.

*The first reversing allocation* along $s$ attains the minimum slope at $s$ just above $s^*$, holding $\lambda$ and $\delta$ fixed. *The least-departure reversal* minimizes $\sum_i|\sum_jF_{ij,\mathrm{cons}}-a^F_{i,\mathrm{cons}}\sum_{j,c}F_{ijc}|+\sum_i|P_{i,\mathrm{cons}}-\tilde a_{i,\mathrm{cons}}P_{i\cdot}|$ subject to a non-positive slope, one LP over all jurisdictions coupled by the slope row. Each definition uses a different criterion for the smallest reversal; the second can concentrate departures in neighborhoods with the largest regression weights.

*Guaranteed value of a report* $S\ell$: $W^{\max}_S=\max\{c^\top(\ell-\ell'):\ell,\ell'\in\Lambda,\ S\ell=S\ell'\}$. For any true allocation $\ell^0$, every $\ell$ with $S\ell=S\ell^0$ forms a feasible pair with it, so the range left after the report is at most $W^{\max}_S$ for every $\ell^0$ and equals it for some. It separates into one LP per jurisdiction. *Revealing the direction.* Report $S$ reveals the direction of the slope on $\Lambda$ iff no two allocations $\ell,\ell'\in\Lambda$ with $S\ell=S\ell'$ have slopes of strictly opposite sign, $\theta(\ell)<0<\theta(\ell')$. Allocations with $\theta=0$ count as neither sign, so full disclosure ($S\ell=S\ell'\Rightarrow\ell=\ell'$) always reveals the direction. Let $t^*_S=\max\{t:\theta(\ell)\le-t,\ \theta(\ell')\ge t,\ S\ell=S\ell',\ \ell,\ell'\in\Lambda\}$, one LP over all jurisdictions. Because the set of pairs is symmetric in $(\ell,\ell')$, a strictly opposite pair exists iff $t^*_S>0$, and $t^*_S$ is then the largest margin of such a pair. Hence $S$ reveals the direction iff $t^*_S\le0$. Table C16 reports $t^*_S$. Under every assumption set and report we consider, $t^*_S>0$ wherever the current set contains zero; in 2022 under the main assumptions $t^*_S=0.026$ for residence reporting.

*Primary suppression.* Let $R_k$ release each integer out-of-zone count $P_{ic}$ exactly when it is at least $k$, otherwise releasing a suppressed marker. It includes invalid ballots and leaves other pooled modes pooled. If $R_k(\ell)=R_k(\ell')$, an unsuppressed count agrees and two suppressed counts belong to $\{0,\ldots,k-1\}$. Consequently $|S(\ell-\ell')|\le k-1$ componentwise, where $S$ selects $P_{ic}$. Let
$$\overline W_k=\max\{c^\top(\ell-\ell'):\ell,\ell'\in\Lambda,\ |S(\ell-\ell')|\le k-1\}.$$
Every same-report integer pair is feasible for this continuous relaxation. Therefore the width left by $R_k$ for any feasible integer allocation is at most $\overline W_k$. Relative to the current continuous width $W_0$, at least $1-\overline W_k/W_0$ of that reported range is removed. This is not a fraction of an exactly solved integer prior range. The relaxation need not be sharp: it also allows differences in counts that would be visible and does not impose common suppression markers. At $k=1$ it reproduces exact disclosure. Increasing $k$ weakly increases $\overline W_k$. Table C26 uses $k\in\{1,5,10,20\}$. The rule excludes complementary suppression of larger cells; no disclosure-risk guarantee is claimed.

## A.4 Computation

Each jurisdiction is one LP with $n^2|\mathcal C|+2n|\mathcal C|+n$ variables ($|\mathcal C|=6$). All restrictions are built by one routine used by every computation, including the valid-vote programs and the integer checks. Programs are solved with HiGHS through SciPy, with objective coefficients normalized to unit maximum (without it, coefficients of order $10^{-9}$ fall below the solver's dual tolerance and bounds are reported too narrow) and feasibility tolerances of $10^{-9}$ and $10^{-10}$. Exact dong-level valid-vote bounds use Dinkelbach's (1967) algorithm. Table A1 re-solves selected near-zero lower bounds as mixed-integer programs with a 30-second limit, extended to 180 seconds if no integer allocation is found. These optimization checks exclude the residents' early-composition restriction, for which optimization did not finish within an hour.

<!-- table: tableA1 -->

Table A2 addresses integer feasibility and near-attainability under the main assumptions directly. For each jurisdiction and each continuous endpoint in the four elections from 2022, a zero-objective integer program searches within the endpoint's floor/ceiling box, expanding the box by one and then four ballots if needed, with a three-second limit at each attempt. All 246 searches found integer allocations. A separate checker reads the saved counts and evaluates (R), (S), (Z), the movement cap and both composition restrictions arithmetically, without using the optimization constraint matrices. The witnesses bracket each integer endpoint within 0.0008 of its continuous bound for all Seoul and without the three southeastern districts, less than 0.06 percentage points for a doubling of prices. They establish integer feasibility, positive and negative attainable slopes in the unresolved cases, and near-attainability, rather than proven integer optimality. The reported continuous bounds remain conservative outer bounds for integer ballots.

<!-- table: tableA2 -->

# B. Data

**B.1 Returns and rolls.** Returns are the National Election Commission's counting-unit files (2012–2025) and counting-unit spreadsheets (2026) (National Election Commission 2026). Each dong contributes its election-day voting districts and its in-zone early station; each gu, or constituency in 2024, its out-of-zone early, at-home (and shipboard) and overseas rows. Certified electorates by dong come from the NEC electorate service; in presidential and mayoral elections its totals equal the counting files' totals in all 25 gu. In presidential elections overseas electors with resident registration are assigned to dongs in $E_i$ and are not on the election-day roll. In 2024 the service exceeds the constituency files by 11,672 electors (0.14%), overseas electors without resident registration who vote only for the party list; they are added to $U$. $U$ is non-negative in every unit and differs from the published abstentions of the pooled modes by $-2$ to 57 per gu; positive differences are in-zone early abstentions, and the small negative differences reflect minor inconsistencies between the certified electorate and the counting files. $U$ is small, 0.33%, 0.40%, 0.25% and 0.03% of $H$ in 2022, 2024, 2025 and 2026 (Table C25), and larger in higher-price districts, where more residents are registered abroad; it is allocated among a jurisdiction's dongs without restriction.

*Election coverage.* The six elections are assembled cases, not a prespecified or exhaustive sample. Other legislative and local contests, including the 2020 National Assembly and 2022 local elections, are outside this dataset. Their omission does not imply unavailable source data. The comparisons therefore concern the included contests, rather than a continuous trend or a representative difference between election types. The estimands use registered residence, which can differ from actual residence for students, soldiers and residents abroad.

In 2022, voters with COVID-19 voted early in a separate session on the second early-voting day or on election day after regular hours; the counting-unit files contain no separate category for these ballots, which are reported within the standard modes and treated accordingly.

**B.2 The 2026 zones.** When local councils and heads are elected together at the end of their terms, the early-voting zone is the district-council constituency (Regulations on Public Official Elections, Art. 133(3); National Election Commission n.d.); in presidential elections it is the gu, and in National Assembly elections the constituency where a gu holds two or more (Art. 86(3)). The NEC's table of council constituencies and dongs (*Table of Constituencies and Eup, Myeon and Dong*, 선거구 및 읍면동현황) assigns each of Seoul's 427 dongs to one of 155 constituencies. For the 113 contested constituencies, the council returns list the same dongs and report out-of-zone early and at-home voters. A voter receives all ballots at once, so out-of-zone status is the same in every contest: wherever all of a gu's constituencies were contested, the council counts sum exactly to the mayoral gu count, and at each of the 320 in-zone early stations of contested constituencies the council and mayoral counts of early voters are equal (Table B1).

<!-- table: tableB1 -->

**B.3 Prices.** Apartment transactions in the twelve complete calendar months ending before each election month (Ministry of Land, Infrastructure and Transport 2026) are geocoded from lot number to administrative dong through the road-name address service (91% to over 99% matched exactly; the rest by same-lot or nearest-lot majority within the legal dong, or dropped) and mapped to the dong names in force at each election (Yongdu-dong and Sinseol-dong to Yongsin-dong; Gaepo 3-dong to Irwon 2-dong before 2023; the five Sindang dongs to their pre-2014 names in 2012; Sangil 1- and 2-dong to Sangil-dong and Hang-dong to Oryu 2-dong in 2017). The regressor is the log median price per square meter. In 2017–2026 the median dong has 70–200 transactions; dongs with fewer than 30 number 99, 38, 96, 109, 62 and 43 in 2012, 2017, 2022, 2024, 2025 and 2026.

The supplied price summaries are frozen analysis inputs. Reconstructing available summaries from the saved trades and current address crosswalk reproduces the 2022, 2024 and 2026 medians. One 2012 and two 2017 medians differ by at most 0.65%; checking accounting-only and minimal-movement/10-point slopes in both geographic scopes changes endpoints by less than 0.00004 and no sign conclusions (supplementary price-construction audit). The original 2025 transaction download and generating code remain unavailable. To audit that year's input, we separately retrieved all 300 Seoul district-months for June 2024–May 2025 from MOLIT on 14 October 2026: 73,319 records, of which 68,448 remain after cancellation flags are excluded. Extending the saved address crosswalk maps 68,356 of these records (99.87%) and yields prices for 421 neighborhoods, compared with 420 in the archived summary; 419 have prices in both. The median absolute price difference on common neighborhoods is 0.003%, but 56 differ by more than 1%; the maximum is 75.4% in Jangchung-dong, with three archived transactions versus two in the rebuild. The two log-price measures correlate at 0.996. These differences can combine source revisions and mapping changes, which this audit cannot separate. Recomputing the A, C, D and E slope ranges changes endpoints by at most 0.012 and leaves their sign conclusions unchanged in both geographic scopes. Table C28 also compares the main setting on common geographic support. Raw XML, request dates and hashes, the extended address map, reconstruction code and comparison files are supplied. This is a reproducible alternative measurement, not recovery of the original snapshot.

**B.4 Mobility.** Seoul Living Mobility (Seoul Metropolitan Government and KT 2026) reports trips by origin and destination dong, day and hour, with a stay of at least 27 minutes; counts of three or fewer are suppressed. We keep home-origin trips from Seoul arriving 06:00–17:59 on the two weekdays of early voting (Friday and Saturday; Thursday and Friday in 2025), summed over the month's days with those weekdays; a calibration from each day alone gives nearly the same bounds (supplementary day-specific calibration check). For zone $u$, $W_u$ counts trips to another dong of $u$ and $X_u$ trips leaving $u$; $R_u=W_u/X_u$ and $C_u=R_uB_u$, with $B_u$ the zone's out-of-zone early ballots (in 2026 the council headcount for contested constituencies, scaled to counted mayoral ballots, and otherwise the gu residual split in proportion to removed residents who did not vote at an in-zone station, $E-D-K$); $C_u$ is allocated to stations by their inflow from other dongs of $u$. Suppressed counts are set to 2. The mobility data use an older dong system in a few places, where one code covers two election dongs (Sangil 1- and 2-dong; Oryu 2-dong and Hang-dong; Sinseol-dong and Yongdu-dong); trips of such a code are split between its dongs in proportion to their electorates, and in the one 2026 zone that consists only of two such dongs, where movement between them is unobservable, $R_u$ is set to the median of the other zones with two or more dongs. Calibrated flows are a median 9–21% of a station's ballots in 2022–2025 and 4% in 2026.

**B.5 Counting rules elsewhere.**

<!-- table: tableB2 -->

*Sources.* Taiwan: Civil Servants Election and Recall Act, Art. 17 (Taiwan n.d.a, n.d.b). Japan: Public Offices Election Act, Arts. 18 and 66(2) (Japan 1950). United States: Amos et al. (2017); Palmer and Schneer (2021). Germany: Bundeswahlordnung § 7 (Germany 2002); postal ballots were 47.3% of ballots in 2021 and 37.0% in 2025 (Die Bundeswahlleiterin 2025). Canada: Canada Elections Act, s. 168(1) (Canada 2000); Elections Canada (2025, Table 5). Australia: Australian Electoral Commission (2025).

# C. Results cited in the text

Table C1 gives identified sets under uniform movement for all elections, citywide and within gu, with breakdown points. Table C2 shows what the 2026 zones and the council contest's headcounts add (Section 4.4). Tables C3–C7 concern the assumptions of Section 4.5: mobility-calibrated movement, the region where the within-district slope is positive, the allocations that reverse it, and restrictions on how movers vote. Tables C8–C11 are robustness checks: the early-vote gap and price, the out-of-zone benchmark, alternative specifications and the neighborhood contrast. Table C12 reports guaranteed reporting gains, Table C13 the sensitivity to price measurement, Table C14 the regressions across districts, Table C15 valid-vote shares, Table C16 whether a report reveals the direction of the slope, Table C17 the analysis without Gangnam, Seocho and Songpa (Section 4.3) for columns A–E of Table 2, Table C18 the same for valid-vote shares, Table C19 how far the residents' early-composition assumption can be relaxed with and without the three districts, Table C20 the point-identified benchmarks: election-day voters and in-zone station shares (Section 4.2), Table C21 the observed gaps between out-of-zone and in-zone early voters that serve as a reference for the out-of-zone tolerance (Section 3.4), Table C22 the restriction on price-aligned departures, Table C23 age composition and the tercile contrast, and Table C24 alternative outcomes, including the combined conservative vote in 2017, Table C25 further restrictions: the largest out-of-zone tolerance, movers' composition together with residents' composition, and price-aligned out-of-zone departures; Table C26 gives conservative reporting gains under primary suppression, Table C27 the feasibility-based tolerance comparison, Table C28 the alternative 2025 price reconstruction, and Table C29 the joint geographic and price-tail sensitivity.

<!-- table: tableC1 -->

<!-- table: tableC2 -->

<!-- table: tableC3 -->

<!-- table: tableC4 -->

<!-- table: tableC5 -->

<!-- table: tableC6 -->

<!-- table: tableC7 -->

<!-- table: tableC8 -->

<!-- table: tableC9 -->

<!-- table: tableC10 -->

<!-- table: tableC11 -->

<!-- table: tableC12 -->

<!-- table: tableC13 -->

<!-- table: tableC14 -->

<!-- table: tableC15 -->

<!-- table: tableC16 -->

<!-- table: tableC17 -->

<!-- table: tableC18 -->

<!-- table: tableC19 -->

<!-- table: tableC20 -->

<!-- table: tableC21 -->

*Price-aligned departures.* A reversal requires residents' early votes in higher-price neighborhoods to be systematically less conservative than their neighborhoods' election-day votes imply, but the symmetric restrictions let each neighborhood depart independently. We therefore ask what a different restriction would imply: within each counting jurisdiction, the slope of residents' early-vote departures (in-zone and out-of-zone, as a share of the roll) on log price may not exceed $\kappa$ in absolute value (Online Appendix A.1 and Table C22). With the out-of-zone tolerance removed, the slope among all residents stays positive for $\kappa$ up to 0.042, 0.038, 0.032 and 0.095 in 2022, 2024, 2025 and 2026, and up to 0.028, almost zero, 0.011 and 0.075 outside the three districts. Two observable patterns give a scale, though neither measures residents' unobserved departures: the same slope for in-zone station ballots, which also count non-residents, is at most 0.016, 0.047, 0.026 and 0.013 in absolute value across jurisdictions, and the slope implied if early-vote gaps varied with price within counting jurisdictions as they do across them (districts; constituencies in 2024) is 0.007, 0.008, 0.021 and 0.006. For all of Seoul $\kappa^*$ exceeds both scales in 2022, 2025 and 2026 and the between-jurisdiction one in 2024; outside the three districts it exceeds both in 2022 and 2026 and neither in 2024 and 2025. Bounding only the alignment of out-of-zone departures orders the elections similarly (Table C25). These results identify the additional assumption that would settle the undetermined signs; they do not show that it holds.

<!-- table: tableC22 -->

<!-- table: tableC23 -->

<!-- table: tableC24 -->

<!-- table: tableC25 -->

Primary suppression changes the information in a residence report. Table C26 evaluates the explicit rule in Appendix A.3. The percentages compare a conservative upper bound on remaining integer uncertainty with the current continuous range; they do not assume that suppressed cells are known exactly.

<!-- table: tableC26 -->

*Distance from refutation.* For each counting jurisdiction, we find the smallest feasible out-of-zone band with calibrated movement and residents' in-zone slack $s=0.02$ held fixed. Bisection returns a feasible upper endpoint within 0.00001 of the threshold. An empty feasible set means that the restriction contradicts the observed counts, not that a slope is identified. Table C27 adds the same excess tolerance to these jurisdiction-specific thresholds. This separates compatibility with the counts from the constant-band comparison in Table 2. Because some new bands may be smaller and others larger than 0.10, the main and alternative models are not generally nested. Neither compatibility nor stability across these scenarios establishes that a restriction holds for the unobserved ballots.

<!-- table: tableC27 -->

*Newly reconstructed 2025 prices.* Table C28 holds the electoral inputs and allocation restrictions fixed and replaces the archived price summary with a separately reconstructed summary (Appendix B.3). Both price definitions are evaluated on their available neighborhoods. The exercise checks the sensitivity of the historical results; it does not recover the original download or establish the correctness of every historical address assignment.

<!-- table: tableC28 -->

*Price tails beyond the three districts.* Table C29 combines exclusion of Gangnam, Seocho and Songpa with trimming the highest-price neighborhoods among those remaining. The cutoff is computed within the 357 priced neighborhoods outside the three districts; all accounting constraints are retained. Trimming changes the target population, so these comparisons assess the geographic and price-distribution scope of the relation. The separate leave-one-district-out check keeps a positive lower bound for every remaining district omitted under the main assumptions.

<!-- table: tableC29 -->

# D. A published allocation

A polling firm's research note on the 2026 local elections (Lee 2026) reported dong-level correlations between apartment prices and Oh Se-hoon's share in Seoul of 0.84 citywide and 0.71 within gu, and a within-gu slope of about 1.9 points per 10 million won per pyeong. We followed its description: residents' pooled-mode counts from the roll difference, with at-home counts in proportion to registered at-home voters; out-of-zone ballots at the dong's in-zone early composition; at-home ballots at the dong's overall composition; columns rescaled to the gu × candidate totals; integers by largest remainder; mean price per pyeong over June 2025 to May 2026. On 423 dongs (424 in the original) this gives 0.842, 0.709 and 1.88, matching the reported figures to their precision.

The replication permits three separate checks. The allocation reproduces the official gu totals by construction. Its premise that residents' out-of-zone ballots have their station's composition cannot hold exactly, because out-of-zone early voters were more favorable to Oh than in-zone early voters in every gu (median 3.6 points, Table C21); the rescaling changes the premise. The allocation does not satisfy every accounting restriction: its constituency-level out-of-zone headcounts are within a median 0.4% of the council returns' counts, but in 47 of 155 constituencies they exceed what the roll leaves for pooled ballots and non-voting, by a median of 16 voters (Table D1). Its slope of 1.88 lies inside every identified set in Table D2, including the set under the paper's main assumptions ($[1.16,2.54]$), so its positive slope is compatible with the range identified under the main assumptions in 2026.

<!-- table: tableD1 -->

<!-- table: tableD2 -->

# References

Amos, Brian, McDonald, Michael P. and Watkins, Russell (2017) When boundaries collide: Constructing a national database of demographic and voting statistics. *Public Opinion Quarterly* 81(S1), 385-400. <https://doi.org/10.1093/poq/nfx001>

Australian Electoral Commission (2025) *2025 Federal Election Report*. Canberra: AEC. Available at: <https://www.aec.gov.au/Elections/federal_elections/2025/2025-Federal-Election-Report.pdf> (accessed 11 October 2026).

Canada (2000) *Canada Elections Act*, S.C. 2000, c. 9, s. 168. Available at: <https://laws-lois.justice.gc.ca/eng/acts/E-2.01/> (accessed 11 October 2026).

Die Bundeswahlleiterin (2025) *Wahl zum 21. Deutschen Bundestag am 23. Februar 2025* (Election to the 21st German Bundestag on 23 February 2025), Heft 5, Teil 2 (Booklet 5, Part 2). Wiesbaden [in German]. Available at: <https://bundeswahlleiterin.de/> (accessed 11 October 2026).

Dinkelbach, Werner (1967) On nonlinear fractional programming. *Management Science* 13(7), 492-498. <https://doi.org/10.1287/mnsc.13.7.492>

Elections Canada (2025) *Forty-Fifth General Election 2025: Official Voting Results*, Table 5. Available at: <https://www.elections.ca/res/rep/off/ovrGE45/62/table5E.html> (accessed 11 October 2026).

Germany (2002) *Bundeswahlordnung* [Federal Electoral Regulations], as promulgated 19 April 2002, § 7. Available at: <https://www.gesetze-im-internet.de/bwo_1985/> (accessed 11 October 2026).

Japan (1950) 公職選挙法 [Public Offices Election Act], Act No. 100 of 1950, Articles 18 and 66(2). e-Gov Laws. Available at: <https://laws.e-gov.go.jp/law/325AC1000000100> (accessed 10 October 2026).

Lee, Dong-han (2026) [9hoe jiseon teukjip] budongsangwa sudogwon eummyeondong pyosim bunseok (Ninth local elections: Real estate and voting patterns in the capital region's eups, myeons and dongs). *Hankook Research: Public Opinion within Public Opinion*, 10 June. Research note [in Korean]. Available at: <https://hrcopinion.co.kr/archives/36779> (accessed 10 October 2026).

Ministry of Land, Infrastructure and Transport (2026) Apartment sale transactions, detailed records (RTMSDataSvcAptTradeDev), monthly records for Seoul in the twelve months before each election studied (December 2011 to May 2026). Public Data Portal [in Korean]. Available at: <https://www.data.go.kr/> (accessed 10 October 2026).

National Election Commission (2026) *Election Statistics System* and *Public Data Portal* files: counting-unit returns (중앙선거관리위원회_대통령선거 개표결과, files for 19 December 2012, 9 May 2017, 9 March 2022 and 3 June 2025; 중앙선거관리위원회_국회의원선거 개표결과, 10 April 2024); counting-unit spreadsheets for the 3 June 2026 Seoul mayoral election, by district; certified electorates by dong (ElcntInfoInqireService, getEmdElcntInfoInqire, data.go.kr); the table of constituencies and dongs (선거구 및 읍면동현황) and district-council returns for 3 June 2026. Available at: <https://info.nec.go.kr/> and <https://www.data.go.kr/> (accessed 11 October 2026).

National Election Commission (n.d.) Regulations on Public Official Elections, Articles 86(3) and 133(3), in the versions in force at each election studied; Article 86(3) as amended 24 December 2015 and Article 133(3) as amended 9 March 2018. Korean Law Information Center [in Korean]. Available at: <https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EA%B3%B5%EC%A7%81%EC%84%A0%EA%B1%B0%EA%B4%80%EB%A6%AC%EA%B7%9C%EC%B9%99> (accessed 12 October 2026).

Palmer, Maxwell and Schneer, Benjamin (2021) *Racially Polarized Voting Analysis for the Virginia Redistricting Commission*. Report, 31 August. Available at: <https://virginiaredistricting.org/2021/Data/Publications/palmer_schneer_rpv_report.pdf> (accessed 10 October 2026).

Seoul Metropolitan Government and KT (2026) *Seoul Living Mobility: Administrative-dong data*. Seoul Open Data Plaza [in Korean]. Available at: <https://data.seoul.go.kr/dataVisual/seoul/seoulLivingMigration.do> (accessed 10 October 2026).

Taiwan (n.d.a) 公職人員選舉罷免法 [Civil Servants Election and Recall Act], Article 17. Available at: <https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=D0020010> (accessed 10 October 2026).

Taiwan (n.d.b) 總統副總統選舉罷免法 [Presidential and Vice Presidential Election and Recall Act]. Available at: <https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=D0020053> (accessed 10 October 2026).
