import os
from dotenv import load_dotenv
import requests

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

OUTREACH_DIR = os.path.dirname(__file__)
OUTPUT_FILE = os.path.join(OUTREACH_DIR, 'reddit_posts.txt')


def draft_reddit_posts():
    groq_key = os.getenv('GROQ_API_KEY')

    response = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {groq_key}',
            'Content-Type': 'application/json',
        },
        json={
            'model': 'llama-3.1-8b-instant',
            'max_tokens': 3000,
            'messages': [
                {
                    'role': 'user',
                    'content': (
                        'Write 3 Reddit posts that are pure value — no product links in the body. '
                        'Post 1 for r/ChatGPT: share 3 genuinely useful, specific AI prompts for YouTube creators '
                        '— the kind that save real time on scripting, titles, or research. '
                        'Post 2 for r/artificial: share insights on how AI prompt engineering is changing content '
                        'creation workflows, with concrete before/after examples. '
                        'Post 3 for r/passive_income: share a realistic breakdown of how someone could create and '
                        'sell a digital AI prompt pack — the process, effort, and what actually works. '
                        'Rules: sound like a real human, lead with genuine value, no clickbait titles, '
                        'no product links anywhere in the body. '
                        'End every post body with exactly this sentence: '
                        '"I packaged these into a full prompt pack — comment or DM if you want the link." '
                        'Format each post as: SUBREDDIT: r/... then TITLE: ... then BODY: ...'
                    ),
                }
            ],
        },
    )
    response.raise_for_status()
    content = response.json()['choices'][0]['message']['content']

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print('\n' + '=' * 60)
    print(content)
    print('=' * 60 + '\n')
    print(f'Saved to: {OUTPUT_FILE}')

    return content


if __name__ == '__main__':
    draft_reddit_posts()
    print('YOUR ONLY JOB: Go post these 3 posts on Reddit. Come back when done.')
