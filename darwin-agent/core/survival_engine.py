import os
import json
import subprocess
import sys
from dotenv import load_dotenv
import requests

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

CORE_DIR = os.path.dirname(__file__)
STATE_FILE = os.path.join(CORE_DIR, 'state.json')
PRODUCTS_DIR = os.path.join(CORE_DIR, '..', 'products')
OUTREACH_DIR = os.path.join(CORE_DIR, '..', 'outreach')


def check_sales():
    token = os.getenv('GUMROAD_TOKEN')
    response = requests.get(
        'https://api.gumroad.com/v2/sales',
        headers={'Authorization': f'Bearer {token}'},
    )
    response.raise_for_status()
    data = response.json()
    sales = data.get('sales', [])
    return len(sales)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'status': 'alive',
        'survival_days': 0,
        'death_countdown': 7,
        'last_sales': 0,
    }


def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


def run_survival_check():
    state = load_state()
    current_sales = check_sales()
    last_sales = state['last_sales']
    new_sales = current_sales - last_sales

    if new_sales > 0:
        print(f'ALIVE - earned today ({new_sales} new sale(s))')
        state['status'] = 'alive'
        state['survival_days'] += 1
        state['death_countdown'] = 7
        state['last_sales'] = current_sales
    else:
        state['death_countdown'] -= 1
        days_left = state['death_countdown']

        if days_left <= 0:
            print('PIVOTING TO NEW NICHE')
            state['death_countdown'] = 7
            state['status'] = 'pivoting'
            save_state(state)

            print('  Running product_creator.py...')
            subprocess.run(
                [sys.executable, os.path.join(PRODUCTS_DIR, 'product_creator.py')],
                check=True,
            )

            print('  Running gumroad_lister.py...')
            subprocess.run(
                [sys.executable, os.path.join(PRODUCTS_DIR, 'gumroad_lister.py')],
                check=True,
            )

            print('  Running reddit_drafter.py...')
            subprocess.run(
                [sys.executable, os.path.join(OUTREACH_DIR, 'reddit_drafter.py')],
                check=True,
            )

            state['status'] = 'alive'
        else:
            print(f'WARNING - {days_left} day(s) until pivot')
            state['status'] = 'warning'

    save_state(state)

    print('\n--- STATE SUMMARY ---')
    print(f'  Status:         {state["status"]}')
    print(f'  Survival days:  {state["survival_days"]}')
    print(f'  Death countdown:{state["death_countdown"]}')
    print(f'  Total sales:    {state["last_sales"]}')
    print('---------------------')


if __name__ == '__main__':
    run_survival_check()
