# TODO (morning, 8 Oct): needs Achintya

Everything through P6 is pushed and CI + Pages are green. These need your login or a decision:

1. **Deploy the Streamlit app** (needs your GitHub login on share.streamlit.io):
   share.streamlit.io → *Create app* → *Deploy a public app from GitHub* → repo `achintya007-arch/qfolio`,
   branch `main`, main file `app/streamlit_app.py` → *Advanced settings*: Python 3.12 → custom subdomain
   `qfolio` → *Deploy*. Then click "Find the basket" once to check that the live solve works on Linux
   (it runs in a spawn subprocess; see the NOTE in `solver_pool`).
2. **Check the Pages report** at https://achintya007-arch.github.io/qfolio/ (built from the committed `results/`).
3. **Know the headline caveat before the demo:** on the real NSE instance the optimum and the runner-up differ
   by only 0.004 in cost (1.4 % of the range). XY-QAOA's P(optimal) there is 0.06–0.13 (random 0.05), but
   P(top-2) is 0.35–0.51 (random 0.10). Lead with AR and P(top-2) for that instance and with the 24-instance
   means for P(optimal).
4. **Streamlit deprecation (harmless):** none left in our code; warnings in the log come from the library.
5. **Remaining plan items:** P8 (brief, `fill_readme.py`, demo script numbers) and P9 (fresh-clone check, tag `v1.0.0`).
