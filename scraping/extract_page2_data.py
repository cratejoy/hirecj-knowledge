#!/usr/bin/env python3
"""
Extract data from page 2 of the forum
"""

import json
from datetime import datetime

# Data from page 2
page2_posts = [
    {
        'author': 'David Pitlyuk',
        'title': "Shopify Summer Editions '25",
        'url': '/t/shopify-summer-editions-25/86588',
        'category': 'Shopify',
        'tags': [],
        'replies': 13,
        'views': 259,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Dana Eriksson',
        'title': 'Congratulations to these 6 Delta New Members on Becoming Full ECFers!',
        'url': '/t/congratulations-to-these-6-delta-new-members-on-becoming-full-ecfers/86899',
        'category': 'Delta Cohort',
        'tags': [],
        'replies': 0,
        'views': 14,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'AndrewYouderian',
        'title': 'Partnering Up with the Operators Podcast',
        'url': '/t/partnering-up-with-the-operators-podcast/86681',
        'category': 'Community and Personal',
        'tags': ['operators', 'podcast'],
        'replies': 9,
        'views': 306,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Steven',
        'title': 'Anyone Using Loop Returns?',
        'url': '/t/anyone-using-loop-returns/56180',
        'category': 'SAAS Apps and Software',
        'tags': [],
        'replies': 9,
        'views': 122,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Dana Eriksson',
        'title': 'Welcome Dean Leibbrandt - Swinging into Global Growth with Nakie',
        'url': '/t/welcome-dean-leibbrandt-swinging-into-global-growth-with-nakie/86758',
        'category': 'Delta Cohort',
        'tags': [],
        'replies': 4,
        'views': 13,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Ryan Oliver',
        'title': 'The Hidden Costs of Complexity: Lessons from My eCommerce Evolution',
        'url': '/t/the-hidden-costs-of-complexity-lessons-from-my-ecommerce-evolution/85246',
        'category': 'Operations and Logistics',
        'tags': ['drop-shipping', 'experience-share'],
        'replies': 13,
        'views': 295,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Kenneth Loricchio',
        'title': 'White Label To Acquisition: How We Turned Excess Manufacturing Capacity Into A Strategic Advantage',
        'url': '/t/white-label-to-acquisition-how-we-turned-excess-manufacturing-capacity-into-a-strategic-advantage/84170',
        'category': 'Manufacturing',
        'tags': ['experience-share'],
        'replies': 4,
        'views': 86,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Nate Dadosky',
        'title': 'Are These USPS Ground Advantage Rates High?',
        'url': '/t/are-these-usps-ground-advantage-rates-high/86882',
        'category': 'Shipping',
        'tags': [],
        'replies': 11,
        'views': 50,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Hasan Hasmani',
        'title': 'Cash-Flowing Current Brand - Looking for New Opportunities',
        'url': '/t/cash-flowing-current-brand-looking-for-new-opportunities/86812',
        'category': 'Misc. eCommerce and Business',
        'tags': [],
        'replies': 7,
        'views': 133,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Tom Shankle',
        'title': "Who's Managing Shipping In-House (without a 3PL)? Has Anyone Tried Amazon Shipping?",
        'url': '/t/whos-managing-shipping-in-house-without-a-3pl-has-anyone-tried-amazon-shipping/86734',
        'category': 'Shipping',
        'tags': [],
        'replies': 18,
        'views': 141,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Shane Rostad',
        'title': 'Does High Growth Require a Higher % of Spend on Opex?',
        'url': '/t/does-high-growth-require-a-higher-of-spend-on-opex/86854',
        'category': 'Operations and Logistics',
        'tags': ['strategy-and-vision'],
        'replies': 6,
        'views': 77,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Dana Eriksson',
        'title': 'Made in the USA: Virtual Hangout on US Manufacturing - Thurs, May 29th, 2025',
        'url': '/t/made-in-the-usa-virtual-hangout-on-us-manufacturing-thurs-may-29th-2025/86577',
        'category': 'ECF Events and Meetups',
        'tags': [],
        'replies': 11,
        'views': 141,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Casey Cutsail',
        'title': 'Free Label Processing Software - Amazon Acquires Veeqo',
        'url': '/t/free-label-processing-software-amazon-acquires-veeqo/64370',
        'category': 'SAAS Apps and Software',
        'tags': [],
        'replies': 126,
        'views': 772,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Padraic Ryan',
        'title': 'ECF Think Tank: Using AI To Hire A Players | Wed, Jan 15th, 3PM EST',
        'url': '/t/ecf-think-tank-using-ai-to-hire-a-players-wed-jan-15th-3pm-est/83335',
        'category': 'ECF Events and Meetups',
        'tags': ['think-tank'],
        'replies': 20,
        'views': 249,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Jeff Chambliss',
        'title': 'Negotiated Rates with USPS Shipping and ShipStation',
        'url': '/t/negotiated-rates-with-usps-shipping-and-shipstation/85132',
        'category': 'Shipping',
        'tags': [],
        'replies': 30,
        'views': 191,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Samantha Gardner',
        'title': 'AWD Capacity Limit Message – Is Anyone Else Seeing This Again? (May 2025)',
        'url': '/t/awd-capacity-limit-message-is-anyone-else-seeing-this-again-may-2025/86782',
        'category': 'Amazon',
        'tags': [],
        'replies': 6,
        'views': 63,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'DaveMcGeady',
        'title': 'Any Other ECF Runners / Marathoners?',
        'url': '/t/any-other-ecf-runners-marathoners/51644',
        'category': 'Personal, Experiences and Off-Topic',
        'tags': [],
        'replies': 348,
        'views': 1600,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Sean Frank',
        'title': 'Bonded Warehouses',
        'url': '/t/bonded-warehouses/85453',
        'category': 'Third Party Fulfillment (3PL)',
        'tags': ['tariffs'],
        'replies': 30,
        'views': 546,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Mehtab Bhogal',
        'title': 'Anyone Else Going to Finaloop eCommerce Academy - June 5th, 2025?',
        'url': '/t/anyone-else-going-to-finaloop-ecommerce-academy-june-5th-2025/86832',
        'category': 'Courses & Conferences',
        'tags': [],
        'replies': 5,
        'views': 50,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'LindsayHagerman',
        'title': '1Password and Passkeys - How Are You Handling This with Your Team?',
        'url': '/t/1password-and-passkeys-how-are-you-handling-this-with-your-team/86837',
        'category': 'SAAS Apps and Software',
        'tags': [],
        'replies': 2,
        'views': 46,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Dana Eriksson',
        'title': "US Manufacturing - Consider the Costs - Continuing Today's Discussion",
        'url': '/t/us-manufacturing-consider-the-costs-continuing-todays-discussion/86835',
        'category': 'Manufacturing',
        'tags': [],
        'replies': 5,
        'views': 67,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Sean Frank',
        'title': 'Good CEO Job (PE Owned, 15M Topline) - Let Me Know if You Want an Intro',
        'url': '/t/good-ceo-job-pe-owned-15m-topline-let-me-know-if-you-want-an-intro/86845',
        'category': 'Help Wanted/Help Available',
        'tags': [],
        'replies': 2,
        'views': 138,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Dan Kent',
        'title': "Meta 'Incremental Attribution' Setting - Has Anyone Used It Yet?",
        'url': '/t/meta-incremental-attribution-setting-has-anyone-used-it-yet/86851',
        'category': 'Paid Traffic',
        'tags': ['facebook-ads'],
        'replies': 2,
        'views': 33,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Mehul Patel',
        'title': 'When to Hire HR Internally vs. Using Recruiters ($10M+ Group)',
        'url': '/t/when-to-hire-hr-internally-vs-using-recruiters-10m-group/86629',
        'category': '$10M+ Store Owners Group',
        'tags': [],
        'replies': 14,
        'views': 95,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'TimShaw',
        'title': 'Cash Flow Problems: How Have You Gotten Through It?',
        'url': '/t/cash-flow-problems-how-have-you-gotten-through-it/4269',
        'category': 'Financial',
        'tags': [],
        'replies': 21,
        'views': 86,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    },
    {
        'author': 'Nate Dadosky',
        'title': 'How Real Is "Key Man" Risk to Acquirers?',
        'url': '/t/how-real-is-key-man-risk-to-acquirers/86609',
        'category': 'Buying and Selling Stores',
        'tags': [],
        'replies': 5,
        'views': 142,
        'last_activity': '3d',
        'scraped_at': datetime.now().isoformat()
    }
]

# Add Delta Cohort welcome posts
delta_posts = [
    ('Dana Eriksson', 'Welcome Leo Voloshin - Dreamy Pajamas and Data-Driven Growth', '/t/welcome-leo-voloshin-dreamy-pajamas-and-data-driven-growth/86741', 6, 19, '3d'),
    ('Dana Eriksson', 'Welcome Trung Cao - Creating Cozy Cat Havens With Cattasaurus', '/t/welcome-trung-cao-creating-cozy-cat-havens-with-cattasaurus/86740', 8, 21, '3d'),
    ('Dana Eriksson', 'Welcome Michael Hittle - Building Custom Cabinetry Dreams Across America', '/t/welcome-michael-hittle-building-custom-cabinetry-dreams-across-america/86739', 8, 26, '3d'),
    ('Dana Eriksson', 'Welcome Kevin McQuiston - Keeping It Clean and Scaling Lean', '/t/welcome-kevin-mcquiston-keeping-it-clean-and-scaling-lean/86798', 4, 10, '3d'),
]

for author, title, url, replies, views, last_activity in delta_posts:
    page2_posts.append({
        'author': author,
        'title': title,
        'url': url,
        'category': 'Delta Cohort',
        'tags': [],
        'replies': replies,
        'views': views,
        'last_activity': last_activity,
        'scraped_at': datetime.now().isoformat()
    })

# Save page 2 data
with open('ecommercefuel_page2_posts.json', 'w', encoding='utf-8') as f:
    json.dump(page2_posts, f, indent=2, ensure_ascii=False)

print(f"Extracted {len(page2_posts)} posts from page 2")

# Combine with page 1 data
with open('ecommercefuel_posts.json', 'r', encoding='utf-8') as f:
    page1_posts = json.load(f)

all_posts = page1_posts + page2_posts

# Save combined data
with open('ecommercefuel_all_posts.json', 'w', encoding='utf-8') as f:
    json.dump(all_posts, f, indent=2, ensure_ascii=False)

print(f"Total posts from 2 pages: {len(all_posts)}")

# Generate statistics
categories = {}
authors = {}
tags_count = {}

for post in all_posts:
    # Count categories
    cat = post.get('category', 'Unknown')
    categories[cat] = categories.get(cat, 0) + 1
    
    # Count authors
    author = post.get('author', 'Unknown')
    authors[author] = authors.get(author, 0) + 1
    
    # Count tags
    for tag in post.get('tags', []):
        tags_count[tag] = tags_count.get(tag, 0) + 1

print("\n=== Combined Statistics ===")
print(f"Total unique categories: {len(categories)}")
print(f"Total unique authors: {len(authors)}")
print(f"Total unique tags: {len(tags_count)}")
print(f"Most active category: {max(categories.items(), key=lambda x: x[1])}")
print(f"Most active author: {max(authors.items(), key=lambda x: x[1])}")
print(f"Most replied thread: {max(all_posts, key=lambda x: x['replies'])['title']} ({max(p['replies'] for p in all_posts)} replies)")
print(f"Most viewed thread: {max(all_posts, key=lambda x: x['views'])['title']} ({max(p['views'] for p in all_posts)} views)")