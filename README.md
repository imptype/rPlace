# rPlace
r/Place (renamed later to Pixel Canvas) was my first ever Discord bot. It went through 3 rewrites (`legacy` -> `rewrite` -> `main`). I still think the code was never that good, although completely functional, and at its current state, it's extremely messy to work with.

The bot shutdown because the database it relied heavily upon, provided by [Deta](deta.space), has shutdown. A lot of code would need to be rewritten, not just [database.py](src/utils/database.py), and I don't think it's a worthwhile investment rn.

I used Deta because I thought it would be cool to have an entire bot hosted on the same platform. Bad idea; Deta's servers are in Germany, Discord's servers are in the USA, already that's a massive roundtrip and the ping was bad. So I moved the host to [Vercel](https://vercel.com) to improve the ping, but the database stayed with Deta ever since.

On top of that, the bot still suffers from minor desynchronization randomly, despite putting in a lot of code and checks to prevent that, so really it should've been using Redis / [Vercel KV](https://vercel.com/docs/storage/vercel-kv) to prevent that too.

Use https://github.com/imptype/BasicBot if you're looking for an actual guide to make bots.

🔗 **App Link:** https://discord.com/application-directory/970423357206061056
