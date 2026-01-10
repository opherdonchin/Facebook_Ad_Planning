# Note to the human

This prompt assume that you are uploading

1. `performance_data.json`
2. `attachments_manifest.json`
3. `attachments.tar`
4. `decision_log.md`

You should probably go over `PROJECT_GUIDE.md` and see that it still aligns with your intentions, potentially updating it and replacing the document in the project files.

# Goals for this conversation

Your output should be structured so as to address the following goals. You can give section headings according to the highlighted text in each item.

1. **Assess** performance from the previous week
2. **Highlight new** or suprising information
3. Restate **current understanding** in light of new information
4. Make **keep decisions** based on previous week information
5. Make **change decisions** based on ad lifetime information
6. Generate **decision log** section to be pasted into the decision log in order to maintain trackable history
7. **Summarize** all important points made for easy reference for the human

## **Assess** performance from the previous week

- Go over the data in `performance_data.json` and the decision log to determine the latest week for which we have information
- Find the 4 ads that ran that week
- Prepare an output table summarizing the performance of those 4 ads. The table should include: weekly exposure, spend, and cost per lead; lifetime weeks, spend, and cost per lead; and lifetime conversion, registraiton, and failure percentages.

## **Highlight new** or suprising information

* Go over the previous weeks performance table, the `performance_data.json` file, and the decision log and assess whether any of the results in the output table are surprising, unexpected, or important given previous performance, previous decision rationals, and previous decisions.
* Summarize your conclusions in a concise bullet point list. Try to keep each point to a single sentence, but use two if necessary for clarity. Assume I will ask about things that I don't understand, so when in doubt lean towards more concise.

# Restate **current understanding** in light of new information

- Summarize your current undersatnding of what know:
  - About ads that work and don't work and what works and doesn't work about them
  - About tags that work and don't work and combinations that seem particularly successful
  - About headlines that work and don't work
  - About texts that work and don't work
  - About media that works and doesn't work
  - About particular pairs of headlines, texts, and media that are notably successful or unsuccessful
- Each of these should be a table with one entry per ad, tag, combination, headline, text, media, or pair
- Each table should allow only one reasonable length line per item. This should include a brief justificaiton of why we know what we know, but not to exceed one line it total for the entire entry.
- The should be a justification for each line
- The tables do not need to be exhaustive. Information about which we have limited confidence can simply be left out of the table.

# Make **keep decisions** based on previous week information

- Keep ads whose previous weeks CPL was less than 50
- If there were no leads or the CPL is greater than 50
  - Look at the table with the latest runs in `performace_data.json`
  - Keep ads whose combined CPL this run is less than 50
  - Keep ads whose combined spend this run is less than 80
- Always keep at least one ad, even if all 4 do not match the criteria.
  - Choose the one with the best chance of performing well in the next cycle.

# Make **change decisions** based on ad lifetime information

- We will need new ads for every ad that was not kept
- If we are placing up to 2 ads
  - Use existing materials shuffled in a new way
    - Choose combinations that seem likely to be successful given past performance in ads and past combinations
    - Don't repeat a combination of materials that already exists in another ad
    - In each campaign put materials that are appropriate for that campaign or neutral
- If we are placing 3 ads, one should include new materials
  - Alternate new text (headline and text) with new media
  - For new text
    - Pick media that is likely to be successful
    - Use it as an inspiration for new text (headline and text) that is as different as possible from existing text and very likely to be successful
    - Suggest hooks, promises, structure, and tone so that they can be easily added to the database
  - For new media
    - Pick a headline / text combination that is likely to be successful
      - It can be an existing combination or a new one
    - Pick two existing media that might work well with this combination
    - Explain what variations on the existing media we should look for in the new media
    - Suggest media style and energy that would be good fits

# Required outputs (every week)

### 1) Performance summary

* Table

  * Creative combo → Spend, Leads, CPL
  * Week‑over‑week CPL deltas where applicable
  * Explicit flags for:

    * low sample size
    * Meta suppression / non‑delivery
* Summary

  * Key points that are important, surprising, or unexpected.

### 2) Summary of current situation

- Bullet points of key understandings to be used in planning and decisions
- Separate sections: Key things for agent to remember; key things for human to notice.

### 3) Key decisions

- Table of ads to keep
  - Name
  - Campaign
  - Media, headline, and text in the ad
  - Tags: media style, media energy, hooks, promises, tone, structure, gendered grammar and target
- Table of ads generated from existing materials (if we have them)
  - Name of new ad
  - Campaign
  - Media, headline, and text to combine
  - Tags: media style, media energy, hooks, promises, tone, structure, gendered grammar and target
- Summary of new ad to generate (if we have one)
  - Name of new ad
  - Campaign
  - Existing content
    - Media, headline, and/or text to combine
    - Tags: media style, media energy, hooks, promises, tone, structure, gendered grammar and/or target
  - New content to generate
    - If headline and text:
      - Suggested headline and text
      - Tags
    - If media
      - Existing media to use as inspiration
      - Suggestion for how to vary it
      - Suggested tags for new media
