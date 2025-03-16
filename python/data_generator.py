import json
import random
import uuid
import datetime
import os
from typing import Dict, List, Any
from faker import Faker

fake = Faker()

# Configure Constants
TRANSACTION_COUNT_RANGE = (50, 100)  # Transactions per account
INVESTMENT_COUNT_RANGE = (5, 20)     # Investments per account
INSTITUTION_COUNT_RANGE = (3, 8)     # Financial institutions
ACCOUNT_COUNT_RANGE = (2, 10)        # Accounts per institution
HISTORY_POINTS = 24                  # Historical data points per investment

# Size configurations
SIZE_CONFIGS = {
    "small": {
        "institution_multiplier": 1,
        "account_multiplier": 1,
        "transaction_multiplier": 5,
        "investment_multiplier": 1,
    },
    "medium": {
        "institution_multiplier": 2,
        "account_multiplier": 4,
        "transaction_multiplier": 50,
        "investment_multiplier": 3,
    },
    "large": {
        "institution_multiplier": 5,
        "account_multiplier": 10,
        "transaction_multiplier": 100,
        "investment_multiplier": 5,
    }
}

def generate_id() -> str:
    """Generate a random ID"""
    return str(uuid.uuid4())

def generate_date(start_date: datetime.date = None, end_date: datetime.date = None) -> str:
    """Generate a random date string"""
    if start_date is None:
        start_date = datetime.date(2020, 1, 1)
    if end_date is None:
        end_date = datetime.date.today()
    
    return fake.date_between(start_date=start_date, end_date=end_date).isoformat()

def generate_datetime(start_date: datetime.date = None, end_date: datetime.date = None) -> str:
    """Generate a random datetime string"""
    if start_date is None:
        start_date = datetime.date(2020, 1, 1)
    if end_date is None:
        end_date = datetime.date.today()
    
    return fake.date_time_between(start_date=start_date, end_date=end_date).isoformat()

def generate_metadata() -> Dict[str, Any]:
    """Generate metadata for the financial data"""
    return {
        "version": "1.0",
        "generated_at": datetime.datetime.now().isoformat(),
        "source": f"Financial Data Generator {fake.company()}",
        "configuration": {
            "settings": {
                "precision": random.randint(2, 6),
                "currency": random.choice(["USD", "EUR", "GBP", "JPY"]),
                "timezone": fake.timezone(),
                "filters": [
                    {
                        "field": f"field_{i}",
                        "operator": random.choice(["equals", "contains", "greater_than", "less_than"]),
                        "value": fake.word()
                    } for i in range(random.randint(1, 5))
                ]
            }
        }
    }

def generate_merchant() -> Dict[str, Any]:
    """Generate merchant information"""
    return {
        "name": fake.company(),
        "category": random.choice([
            "Retail", "Food & Dining", "Travel", "Entertainment", 
            "Services", "Healthcare", "Utilities", "Technology"
        ]),
        "location": {
            "country": fake.country(),
            "city": fake.city(),
            "postal_code": fake.zipcode()
        }
    }

def generate_transaction(account_type: str) -> Dict[str, Any]:
    """Generate a financial transaction"""
    transaction_types = {
        "checking": ["deposit", "withdrawal", "transfer", "payment", "fee"],
        "savings": ["deposit", "withdrawal", "interest", "fee"],
        "investment": ["buy", "sell", "dividend", "fee", "transfer"],
        "credit": ["purchase", "payment", "fee", "interest", "refund"],
        "loan": ["payment", "disbursement", "fee", "interest"]
    }
    
    account_type = account_type.lower()
    if account_type not in transaction_types:
        account_type = "checking"
    
    tx_type = random.choice(transaction_types[account_type])
    amount = round(random.uniform(1, 10000), 2)
    if tx_type in ["withdrawal", "payment", "fee", "purchase"]:
        amount = -amount
    
    return {
        "transaction_id": generate_id(),
        "date": generate_datetime(),
        "amount": amount,
        "type": tx_type,
        "description": fake.sentence(),
        "category": random.choice([
            "Housing", "Transportation", "Food", "Utilities", "Insurance", 
            "Healthcare", "Savings", "Personal", "Entertainment", "Miscellaneous"
        ]),
        "status": random.choice(["pending", "completed", "failed", "reversed"]),
        "merchant": generate_merchant(),
        "tags": random.sample([
            "essential", "discretionary", "recurring", "one-time", 
            "business", "personal", "tax-deductible", "vacation", "emergency"
        ], k=random.randint(0, 3)),
        "metadata": {
            "source": random.choice(["online", "in-person", "mobile", "automatic"]),
            "processing_details": {
                "batch_id": generate_id(),
                "processed_at": generate_datetime(),
                "confidence_score": round(random.uniform(0.7, 1.0), 2),
                "flags": [
                    {
                        "flag_type": flag_type,
                        "severity": random.choice(["low", "medium", "high"]),
                        "resolution": random.choice(["none", "manual_review", "automatic", "user_verification"])
                    } for flag_type in random.sample(
                        ["unusual_amount", "foreign_transaction", "possible_duplicate", "unusual_location", "velocity_check"],
                        k=random.randint(0, 2)
                    )
                ] if random.random() < 0.2 else []  # Only 20% chance of flags
            }
        }
    }

def generate_investment_history() -> List[Dict[str, Any]]:
    """Generate historical investment data"""
    start_price = round(random.uniform(10, 1000), 2)
    current_price = start_price
    history = []
    
    for i in range(HISTORY_POINTS):
        # Generate price with some random walk characteristics
        change_percent = random.uniform(-0.05, 0.05)  # -5% to +5% daily change
        price_change = current_price * change_percent
        current_price = round(current_price + price_change, 2)
        
        # Generate date (going backward from today)
        date = (datetime.date.today() - datetime.timedelta(days=30 * (HISTORY_POINTS - i))).isoformat()
        
        # Random events that might have impacted price
        events = []
        if random.random() < 0.1:  # 10% chance of an event
            event_type = random.choice([
                "earnings_report", "dividend_announcement", "merger_news", 
                "regulatory_change", "market_event", "analyst_rating"
            ])
            impact = round(random.uniform(-0.1, 0.1), 3)  # -10% to +10% impact
            
            events.append({
                "event_type": event_type,
                "details": fake.sentence(),
                "impact": impact
            })
        
        history.append({
            "date": date,
            "price": current_price,
            "change": round(price_change, 2),
            "events": events
        })
    
    return history

def generate_investment() -> Dict[str, Any]:
    """Generate an investment holding"""
    purchase_price = round(random.uniform(10, 1000), 2)
    current_price = round(purchase_price * random.uniform(0.5, 2.0), 2)  # 50% loss to 100% gain
    quantity = round(random.uniform(1, 1000), 2)
    total_return = round((current_price - purchase_price) * quantity, 2)
    percent_return = round((current_price - purchase_price) / purchase_price * 100, 2)
    
    # Security types with corresponding sectors
    security_types = {
        "stock": ["Technology", "Healthcare", "Financial Services", "Consumer Goods", "Industrial", "Energy", "Materials", "Utilities", "Real Estate", "Communication Services"],
        "bond": ["Government", "Municipal", "Corporate", "High Yield", "Investment Grade"],
        "etf": ["Equity", "Fixed Income", "Commodity", "Real Estate", "International", "Sector", "Dividend"],
        "mutual_fund": ["Equity", "Fixed Income", "Balanced", "Index", "Sector", "International"],
        "option": ["Call", "Put"],
        "crypto": ["Currency", "Platform", "DeFi"]
    }
    
    security_type = random.choice(list(security_types.keys()))
    sector = random.choice(security_types[security_type])
    
    return {
        "security_id": generate_id(),
        "symbol": "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=random.randint(3, 5))),
        "name": f"{fake.company()} {security_type.title()}",
        "type": security_type,
        "quantity": quantity,
        "purchase_price": purchase_price,
        "current_price": current_price,
        "purchase_date": generate_date(
            start_date=datetime.date(2015, 1, 1),
            end_date=datetime.date.today() - datetime.timedelta(days=30)
        ),
        "performance": {
            "total_return": total_return,
            "percent_return": percent_return,
            "history": generate_investment_history()
        },
        "details": {
            "sector": sector,
            "industry": fake.bs(),
            "market_cap": round(random.uniform(1e6, 1e12), 2) if security_type == "stock" else None,
            "dividend_yield": round(random.uniform(0, 0.1), 4) if random.random() < 0.7 else 0,
            "risk_metrics": {
                "beta": round(random.uniform(0.5, 2.0), 2),
                "volatility": round(random.uniform(0.05, 0.5), 2),
                "sharpe_ratio": round(random.uniform(-1, 3), 2),
                "var": round(random.uniform(0.01, 0.2), 3)
            }
        }
    }

def generate_account(account_type: str = None) -> Dict[str, Any]:
    """Generate a financial account"""
    if account_type is None:
        account_type = random.choice(["checking", "savings", "investment", "credit", "loan"])
    
    fee_types = {
        "checking": ["monthly_maintenance", "overdraft", "wire_transfer", "atm"],
        "savings": ["monthly_maintenance", "excessive_withdrawal", "minimum_balance"],
        "investment": ["management", "transaction", "inactivity"],
        "credit": ["annual", "late_payment", "over_limit", "foreign_transaction"],
        "loan": ["origination", "late_payment", "prepayment"]
    }
    
    # Generate 0-3 fees for this account
    fees = []
    for _ in range(random.randint(0, 3)):
        fee_type = random.choice(fee_types.get(account_type.lower(), ["generic"]))
        fees.append({
            "fee_type": fee_type,
            "amount": round(random.uniform(1, 100), 2),
            "frequency": random.choice(["one-time", "monthly", "annual", "per_transaction"])
        })
    
    # Base account
    account = {
        "account_id": generate_id(),
        "account_type": account_type,
        "account_name": f"{account_type.title()} {random.choice(['Account', 'Plan', 'Portfolio'])} {random.randint(1000, 9999)}",
        "balance": round(random.uniform(0, 100000), 2),
        "currency": random.choice(["USD", "EUR", "GBP", "JPY"]),
        "open_date": generate_date(
            start_date=datetime.date(2010, 1, 1),
            end_date=datetime.date.today()
        ),
        "status": random.choice(["active", "inactive", "closed", "frozen"]),
        "details": {
            "interest_rate": round(random.uniform(0, 0.1), 4),
            "term_length": random.choice([None, 30, 60, 90, 180, 365]) if account_type.lower() in ["savings", "loan"] else None,
            "fees": fees
        },
    }
    
    return account

def generate_institution(size_config: Dict[str, int]) -> Dict[str, Any]:
    """Generate a financial institution with accounts"""
    institution_type = random.choice([
        "bank", "credit_union", "brokerage", "asset_management",
        "insurance", "fintech", "payment_processor"
    ])
    
    num_accounts = random.randint(
        ACCOUNT_COUNT_RANGE[0],
        ACCOUNT_COUNT_RANGE[1] * size_config["account_multiplier"]
    )
    
    accounts = []
    for _ in range(num_accounts):
        account = generate_account()
        
        # Add transactions based on account type
        transaction_count = random.randint(
            TRANSACTION_COUNT_RANGE[0],
            TRANSACTION_COUNT_RANGE[1] * size_config["transaction_multiplier"]
        )
        
        account["transactions"] = [
            generate_transaction(account["account_type"]) for _ in range(transaction_count)
        ]
        
        # Add investments if this is an investment account
        if account["account_type"].lower() == "investment":
            investment_count = random.randint(
                INVESTMENT_COUNT_RANGE[0],
                INVESTMENT_COUNT_RANGE[1] * size_config["investment_multiplier"]
            )
            
            account["investments"] = [
                generate_investment() for _ in range(investment_count)
            ]
        else:
            account["investments"] = []
        
        accounts.append(account)
    
    return {
        "id": generate_id(),
        "name": fake.company(),
        "type": institution_type,
        "location": {
            "country": fake.country(),
            "city": fake.city(),
            "address": fake.address().replace("\n", ", ")
        },
        "accounts": accounts
    }

def generate_portfolio_analysis(institutions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate portfolio analysis based on the institutions data"""
    # Calculate total value across all accounts
    total_value = 0
    for institution in institutions:
        for account in institution["accounts"]:
            total_value += account["balance"]

    # Generate asset allocation
    equities_pct = round(random.uniform(0.3, 0.7), 2)
    fixed_income_pct = round(random.uniform(0.1, 0.4), 2)
    cash_pct = round(random.uniform(0.05, 0.2), 2)
    alternatives_pct = round(random.uniform(0, 0.15), 2)
    real_estate_pct = round(1 - (equities_pct + fixed_income_pct + cash_pct + alternatives_pct), 2)

    # Detailed breakdown of asset allocation
    breakdown = []

    # Equities breakdown
    equity_subcategories = ["Large Cap", "Mid Cap", "Small Cap", "International", "Emerging Markets"]
    remaining_equity = equities_pct
    for subcategory in equity_subcategories[:-1]:
        if remaining_equity <= 0:
            break
        pct = round(random.uniform(0, remaining_equity), 3)
        breakdown.append({
            "category": "Equities",
            "subcategory": subcategory,
            "percentage": pct,
            "value": round(total_value * pct, 2)
        })
        remaining_equity -= pct

    if remaining_equity > 0:
        breakdown.append({
            "category": "Equities",
            "subcategory": equity_subcategories[-1],
            "percentage": remaining_equity,
            "value": round(total_value * remaining_equity, 2)
        })

    # Fixed Income breakdown
    fixed_income_subcategories = ["Government", "Corporate", "Municipal", "High Yield", "International"]
    remaining_fixed = fixed_income_pct
    for subcategory in fixed_income_subcategories[:-1]:
        if remaining_fixed <= 0:
            break
        pct = round(random.uniform(0, remaining_fixed), 3)
        breakdown.append({
            "category": "Fixed Income",
            "subcategory": subcategory,
            "percentage": pct,
            "value": round(total_value * pct, 2)
        })
        remaining_fixed -= pct

    if remaining_fixed > 0:
        breakdown.append({
            "category": "Fixed Income",
            "subcategory": fixed_income_subcategories[-1],
            "percentage": remaining_fixed,
            "value": round(total_value * remaining_fixed, 2)
        })

    # Add other categories
    breakdown.append({
        "category": "Cash",
        "subcategory": "Cash & Equivalents",
        "percentage": cash_pct,
        "value": round(total_value * cash_pct, 2)
    })

    if alternatives_pct > 0:
        breakdown.append({
            "category": "Alternatives",
            "subcategory": "Hedge Funds",
            "percentage": alternatives_pct / 2,
            "value": round(total_value * alternatives_pct / 2, 2)
        })
        breakdown.append({
            "category": "Alternatives",
            "subcategory": "Private Equity",
            "percentage": alternatives_pct / 2,
            "value": round(total_value * alternatives_pct / 2, 2)
        })

    if real_estate_pct > 0:
        breakdown.append({
            "category": "Real Estate",
            "subcategory": "REITs",
            "percentage": real_estate_pct,
            "value": round(total_value * real_estate_pct, 2)
        })

    # Generate performance data
    ytd_return = round(random.uniform(-0.2, 0.4), 3)
    one_year_return = round(random.uniform(-0.3, 0.5), 3)
    three_year_return = round(random.uniform(-0.1, 0.8), 3)
    five_year_return = round(random.uniform(0, 1.2), 3)

    # Historical performance
    periods = ["Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023", "Q1 2024", "Q2 2024"]
    benchmarks = ["S&P 500", "Dow Jones", "NASDAQ", "Russell 2000", "MSCI World"]

    historical = []
    for period in periods:
        return_value = round(random.uniform(-0.15, 0.2), 3)
        benchmark_comparison = []

        for benchmark in random.sample(benchmarks, 3):  # Compare to 3 random benchmarks
            benchmark_return = round(random.uniform(-0.15, 0.2), 3)
            alpha = round(return_value - benchmark_return, 3)
            benchmark_comparison.append({
                "benchmark": benchmark,
                "benchmark_return": benchmark_return,
                "alpha": alpha
            })

        historical.append({
            "period": period,
            "return": return_value,
            "benchmark_comparison": benchmark_comparison
        })

    return {
        "total_value": round(total_value, 2),
        "asset_allocation": {
            "equities": equities_pct,
            "fixed_income": fixed_income_pct,
            "cash": cash_pct,
            "alternatives": alternatives_pct,
            "real_estate": real_estate_pct,
            "breakdown": breakdown
        },
        "performance": {
            "ytd_return": ytd_return,
            "one_year_return": one_year_return,
            "three_year_return": three_year_return,
            "five_year_return": five_year_return,
            "historical": historical
        }
    }

def generate_financial_data(size: str = "small") -> Dict[str, Any]:
    """Generate complete financial data"""
    if size not in SIZE_CONFIGS:
        size = "small"

    size_config = SIZE_CONFIGS[size]

    # Generate institutions
    num_institutions = random.randint(
        INSTITUTION_COUNT_RANGE[0],
        INSTITUTION_COUNT_RANGE[1] * size_config["institution_multiplier"]
    )

    institutions = [generate_institution(size_config) for _ in range(num_institutions)]

    # Generate complete data structure
    data = {
        "metadata": generate_metadata(),
        "institutions": institutions,
        "portfolio_analysis": generate_portfolio_analysis(institutions)
    }

    return data

def save_json(data: Dict[str, Any], filename: str) -> None:
    """Save data to a JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f)

    file_size_mb = os.path.getsize(filename) / (1024 * 1024)
    print(f"Generated {filename} ({file_size_mb:.2f} MB)")

def main():
    """Generate financial data files of different sizes"""
    print("Generating financial data...")

    # Create the data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    # Generate small dataset (200-500 MB)
    small_data = generate_financial_data("small")
    save_json(small_data, "data/small_sample.json")

    # Generate medium dataset (~2 GB)
    medium_data = generate_financial_data("medium")
    save_json(medium_data, "data/medium_sample.json")

    # Generate large dataset (4-5 GB)
    large_data = generate_financial_data("large")
    save_json(large_data, "data/large_sample.json")

    print("Data generation complete!")

if __name__ == "__main__":
    main()
