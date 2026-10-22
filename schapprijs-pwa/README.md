# Schapprijs

Compare supermarket prices in the Netherlands, keep shopping lists and spot price drops.
This folder is the installable version of the app: it gets its own icon on Android, iPhone and computers,
works offline, and refreshes its prices every morning for free on GitHub.

## What's in here

| File | What it does |
|---|---|
| `index.html` | The app itself |
| `manifest.webmanifest` | Name, colours and icons, so phones can install it as an app |
| `sw.js` | Makes the app installable and keeps it working offline |
| `icons/` | The cart-and-euro icon in every size phones and computers ask for |
| `scripts/build_data.py` | Turns the open Checkjebon price data into the app's price, history and price-drop files |
| `.github/workflows/update-prices.yml` | Runs the script every morning and publishes the app |

The price files are not in this folder; the daily job builds them fresh each time.

## Put it online (one time, about 10 minutes)

1. **Make a GitHub account** at github.com if you don't have one (free).
2. **Create a repository**: click **New**, name it `schapprijs`, choose **Public**, and click **Create repository**.
   (GitHub Pages is free for public repositories. Your shopping lists are never uploaded; they stay on each phone.)
3. **Upload the files**: on the new repository page click **uploading an existing file**, drag in everything from this folder
   (including the hidden `.github` folder; on a Mac press Cmd+Shift+. in Finder to see it), and click **Commit changes**.
   If the upload skips `.github`, create the file by hand: **Add file → Create new file**, name it
   `.github/workflows/update-prices.yml`, and paste in the contents of that file.
4. **Switch on GitHub Pages**: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
5. **Run it the first time**: **Actions → Update prices and publish → Run workflow**. After 2–3 minutes it turns green.
6. Your app is now live at `https://<your-username>.github.io/schapprijs/`.

From then on it rebuilds the prices every morning by itself (about 07:45 in summer, 06:45 in winter).

## Install it on a phone or computer

- **Android (Chrome):** open the link, tap **⋮ → Install app** (or **Add to Home screen**).
- **iPhone (Safari):** open the link, tap **Share → Add to Home Screen**.
- **Computer (Chrome or Edge):** open the link and click the install icon in the address bar.

It then opens full screen with the Schapprijs icon, like any other app. Send the same link to family:
each phone keeps its own lists and settings.

## Optional: Google Play

Once the app is online you can turn it into a Play Store app with PWABuilder (pwabuilder.com): enter your link,
choose **Android**, and follow the steps. Publishing needs a Google Play developer account (one-time fee).

## Good to know

- Prices come from the open data of Checkjebon.nl (github.com/supermarkt/checkjebon) and can differ from the shelf.
- Price drops are shelf-price changes over the last 30 days; Bonus and multi-buy offers are not in the data.
- The Claude-hosted version keeps working separately. Its lists are stored in your Claude account and do not move
  to this version automatically.
