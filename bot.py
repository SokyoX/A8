
name: Drinkit Hourly Report

on:
  schedule:
    - cron: '0 * * * *'

  workflow_dispatch:
    inputs:
      force:
        description: 'Force report even outside working hours'
        required: false
        type: boolean
        default: false

jobs:
  report:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run bot
        env:
          TG_TOKEN: ${{ secrets.9082216783:AAHOjx_lhZCPxbD3rJ2ewHTu15fcOETmxVs }}
          TG_CHAT_ID: ${{ secrets.789279641 }}
          FORCE: ${{ inputs.force && '1' || '0' }}
        run: python bot.py
