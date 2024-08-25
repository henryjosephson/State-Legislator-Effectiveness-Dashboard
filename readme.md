# NY State Legislator Effectiveness Scores

```
bugs to think about:
[ ] almost ten percent of bills have >2 *primary* sponsors?
```

You (hopefully) voted for someone to represent you and your interests in DC — how do you know if they're actually doing it?

The [Center for Effective Lawmaking](https://thelawmakers.org/), a joint project of the University of Virginia and Vanderbilt University, tries to answer that question by ranking lawmakers' ability to get legislation that they've introduced enacted into law. Though their methodology doesn't count other effective things — e.g. working behind the scenes to pass a bill that isn't theirs or serving as a whip or party leader — it's a great start!

Similar projucts don't seem to exist at the state level, though, even though state legislatures get way more done:  New York, Texas, and California passed xx, xx, and xx bills into law in 2023, respectively. Compare this to the paltry [27 bills that the federal government enacted into law that same year](https://www.nytimes.com/2023/12/19/us/politics/bills-laws-2023-house-congress.html).[^1]

> [!NOTE]
> fill in NY, TX, CA numbers

Here, I'm replicating CEL's methodology for New York State, though I plan to eventually expand this to all 50 states states.

Why start with New York? Three main reasons:
1. I live there,
2. I spent a summer as a legislative aide for Alex Bores, who represents the 73rd Assembly District in Albany,
3. This whole project was Alex's idea.

## Methodology
Feel free to skip this if you don't care about the math.

I've reproduced CEL's original formula below. It looks like a beast, but it isn't too bad; you just have to know what everything means.

It has three types of variables:
- Variables for each lawmaker and session:
    - $i$ for each lawmaker, and
    - $t$ for each session of congress;

- Variables for how far in the legislative process any given bill makes it:
    -  $BILL$ for the number of bills **introduced**,
    - $AIC$ for the number of bills which received **action in committee**,
    - $ABC$ for the number of bills which received **action beyond committee**,
    - $PASS$ for the number of bills which **passed their chamber of origin**, and
    - $LAW$ for the number of bills which passed the other chamber, too, i.e. which where **enacted into law**;

- and variables that divide and weight bills by their ambition and scope:  
    - $C$ for the number of commemmoritive bills,
        - $C$ bills are weighted by $\alpha = 1$,
    - $S$ for the number of substantive bills,
        - $C$ bills are weighted by $beta = 5$,
    - $SS$ for the number of substantive and significant bills,
        - $SS$ bills are weighted by $\gamma = 10$.[^2]

With that said, take a deep breath:

$$
LES_{it} = 
\begin{bmatrix}
    \dfrac{
        \alpha BILL_{it}^C 
        + \beta BILL_{it}^S 
        + \gamma BILL_{it}^{SS}
    }{
        \alpha \sum_{j=1}\limits^{N}BILL_{it}^C 
        + \beta \sum_{j=1}\limits^{N} BILL_{it}^S 
        + \sum_{j=1}\limits^{N} \gamma BILL_{it}^{SS}
    }\\
    \\
    + \dfrac{
        \alpha AIC_{it}^C 
        + \beta AIC_{it}^S 
        + \gamma AIC_{it}^{SS}
    }{
        \alpha \sum_{j=1}\limits^{N}AIC_{it}^C 
        + \beta \sum_{j=1}\limits^{N} AIC_{it}^S 
        + \sum_{j=1}\limits^{N} \gamma AIC_{it}^{SS}
    }\\
    \\
    + \dfrac{
        \alpha ABC_{it}^C 
        + \beta ABC_{it}^S 
        + \gamma ABC_{it}^{SS}
    }{
        \alpha \sum_{j=1}\limits^{N}ABC_{it}^C 
        + \beta \sum_{j=1}\limits^{N} ABC_{it}^S 
        + \sum_{j=1}\limits^{N} \gamma ABC_{it}^{SS}
    }\\
    \\
    + \dfrac{
        \alpha PASS_{it}^C 
        + \beta PASS_{it}^S 
        + \gamma PASS_{it}^{SS}
    }{
        \alpha \sum_{j=1}\limits^{N}PASS_{it}^C 
        + \beta \sum_{j=1}\limits^{N} PASS_{it}^S 
        + \sum_{j=1}\limits^{N} \gamma PASS_{it}^{SS}
    }\\
    \\
    + \dfrac{
        \alpha LAW_{it}^C 
        + \beta LAW_{it}^S 
        + \gamma LAW_{it}^{SS}
    }{
        \alpha \sum_{j=1}\limits^{N}LAW_{it}^C 
        + \beta \sum_{j=1}\limits^{N} LAW_{it}^S 
        + \sum_{j=1}\limits^{N} \gamma LAW_{it}^{SS}
    }
\end{bmatrix}

\begin{bmatrix}
    \dfrac{
        N
    }{
        5
    }\\
\end{bmatrix}
$$

As CEL notes, the $\dfrac{N}{5}$ factor normalizes the average LES to 1 in each Congress.

To get from $LES$ to a given legislator's Benchmark Score $\widehat{LES}$, you can use an ordinary least squares regression model to predict a given legislator $i$'s LES in a given congressional session $t$, using the following as predictors:
- Legislator $i$'s seniority in session $t$,[^3]
- An indicator variable for if legislator $i$ was a member of the majority party in session $t$,
- An indicator variable for if legislator $i$ was a committee chair during session $t$, and
- An indicator 

When you write that out as an equation, you get something like this:

$$
\widehat{LES}_{it} = \hat\alpha + Pseniority SenioritYit + Amajority MajoritYi + Bcom chair Com_Chair + Bsubcom chair Subcom_Chairit
$$
First, for each Congress, we estimate an Ordinary Least Squares regression model where the dependent variable is Representative i’s LES, and the independent variables are Representative i’s Seniority, an indicator variable for whether she was a member of the majority party, and indicator variables for whether she held a committee and/or subcommittee chair. After estimating the regression coefficients that correspond to each of the independent variables, we generated linear predicted values for each Representative’s LES in the given Congress.

The predicted value is denoted as the Representative’s “Benchmark Score” that we refer to on the pages of this website. Having identified a Representative’s Benchmark Score, we denote a Representative’s Legislative Effectiveness Score as being “Above Expectations” if the ratio of her Legislative Effectiveness Score to her Benchmark Score is greater than 1.50. We denote a Representative’s Legislative Effectiveness Score as being “Below Expectations” if the ratio of her Legislative Effectiveness Score to her Benchmark Score is less than .50. Finally, we denote a Representative’s Legislative Effectiveness Score as “Meets Expectations” if the ratio of her Legislative Effectiveness Score to her Benchmark Score is between .50 and 1.50. We employ an identical methodology to calculate a Senator’s benchmark score.

## Roadmap
1. [ ] Implement in .ipynbs outputting csvs, publish csvs in repo.

    a. [ ] Simplest ranking: Number of bills introduced, voted on in committee, passed the house, passed both houses, and signed into law per legislator, standardized by the number of bills that are in each category overall.

    b. [ ] Separate bills into substantive and non-substantive, weighting substantive bills 10x. A bill is non-substantive if it is:

        - A home rule bill

        - A chapter amendment

        - An extender

        - A study bill

        do this programmatically with claude-haiku or gpt-4o-mini.

    c. [ ] Give credit for bills that are incorporated into the budget or other bills, in a similar way to CEL:
    > 5-gram Jaccard similarity "coupled with criteria accounting for bill length, introduction dates, companion bills, and other idiosyncrasies of the contemporary lawmaking process in Congress.When a bill’s language is substantially included in another law, the bill’s sponsor receives credit for that bill receiving action beyond committee (ABC), passing its chamber of origin (PASS) and becoming law (LAW), even if the standalone sponsored bill did not advance through such stages."
    - or... legiscan API's `sasts` column has a `similar to` option -- look into that


2. [ ] Make the scripts automatically update at the end of each session. (shouldn't be hard — cron jobs + lookup tables of when sessions end)
    - how account for extensions/special sessions? is there an api for that? don't want to do manually
    - could also just run it every e.g. month... even tho CEL says bad idea in [their FAQ](https://thelawmakers.org/faq):
    > Q: Why can’t I find out the Legislative Effectiveness Score of a Representative or Senator in the current Congress?
    > 
    > As described on the Methodology page, a Representative’s or Senator’s Legislative Effectiveness Score is a parsimonious metric of how successful she was at moving her agenda items through each of five stages in the legislative process, where each agenda item is coded for substantive significance, in comparison to all other members of the House of Representatives (or Senate). In order to calculate this metric, it is necessary to know how successful each member of the House (or Senate) was at advancing her agenda items through Congress, which can only be ascertained at the conclusion of a given Congress. 
    > 
    > Likewise, one aspect of the coding protocol — identifying whether a bill that was introduced in a Congress is “substantive and significant” — can only be ascertained by consulting Congressional Quarterly publications and Project Vote Smart listings, including those that are published up through the conclusion of the relevant Congress. Hence, it is substantively inappropriate (and technically impossible) to replicate our methodology to calculate Legislative Effectiveness Scores for Representatives (or Senators) who are sitting in a current 2-year Congress before that Congress has concluded.
4. [ ] Host this online on my raspberry pi or the UChicago CS department's servers.
3. [ ] Generalize the process to other states.


[^1]:I don't think this is inherent to the federal government's federal-ness: Republicans had a particularly thin majority in 2023, and when you combine this with Kevin McCarthy's notoriously unpopular speakership, an abnormally unproductive year isn't as surprising.
  check above -- check no of bills passed in years where congress isn't so closely contested?
  later: lin reg to see how well margin of party control predicts qty_bills_passed. i bet it's a significant predictor, but not totally linearly, since a party that's totally in control will just break up into smaller parties. See e.g. the collapse of the Whig Supremacy in England in the 1750s [check for a better link](https://en.wikipedia.org/wiki/Whigs_(British_political_party)#Whig_Supremacy) ([maybe this?](https://en.wikipedia.org/wiki/Patriot_Whigs)) and the end of the [Era of Good Feelings](https://en.wikipedia.org/wiki/Era_of_Good_Feelings) in the US during the 1824 election. 
  also check what the most closely-contested state leg is, see if it's comparable to 27 in fed, bc that's *really* bad


[^2]: This section is lifted mostly from CEL's excellent [Methodology page](https://thelawmakers.org/methodology). It's paraphrased here half because I want you to be able to read it without clicking over, and half because I'm the type of nerd for whom writing the $\LaTeX$ helps me understand.
[^3]: There's a whole [formula for calculating seniority in Congress](https://history.house.gov/Institution/Seniority/Terms-of-Service/), reproduced below if you don't want to click, which I'll replicate for the states.
  A legislator's seniority is defined as their position in an ordered list of all members of their house, where the list is sorted in descending order by:
  /- Number of total terms served (subtracting one term from the number of non-consecutive terms), then
  /- Number of consecutive terms served, then
  /- Alphabetically by last name.