"""Customer data generator."""

import random
from datetime import timedelta
from typing import Any

from faker import Faker

from data_generation.config import US_STATES, GenerationConfig


class CustomerGenerator:
    """Generate synthetic customer data."""

    def __init__(self, config: GenerationConfig):
        self.config = config
        self.fake = Faker()
        Faker.seed(config.random_seed)
        random.seed(config.random_seed)

    def generate(self) -> list[dict[str, Any]]:
        """Generate customer records."""
        customers = []

        for i in range(self.config.num_customers):
            customer_id = f"CUST{i + 1:08d}"
            is_business = random.random() < self.config.business_customer_pct

            # Generate customer data
            customer = self._generate_customer(customer_id, is_business, i)
            customers.append(customer)

        return customers

    def _generate_customer(
        self, customer_id: str, is_business: bool, _index: int
    ) -> dict[str, Any]:
        """Generate a single customer record."""
        # Select state based on population weights
        state = random.choices(
            list(US_STATES.keys()),
            weights=list(US_STATES.values()),
            k=1,
        )[0]

        # Generate creation date within range
        days_range = (self.config.end_date - self.config.start_date).days
        created_days_ago = random.randint(0, days_range)
        created_at = self.config.start_date + timedelta(days=created_days_ago)

        # Determine tier based on age and random factor
        account_age_days = (self.config.end_date - created_at).days
        tier = self._determine_tier(account_age_days)

        if is_business:
            name = self.fake.company()
            email = self.fake.company_email()
            phone = self.fake.phone_number()
        else:
            name = self.fake.name()
            email = self.fake.email()
            phone = self.fake.phone_number()

        address = {
            "street": self.fake.street_address(),
            "city": self.fake.city(),
            "state": state,
            "zip_code": self.fake.zipcode_in_state(state) if hasattr(self.fake, 'zipcode_in_state') else self.fake.zipcode(),
            "country": "US",
        }

        return {
            "customer_id": customer_id,
            "customer_type": "business" if is_business else "residential",
            "name": name,
            "email": email,
            "phone": phone,
            "address_street": address["street"],
            "address_city": address["city"],
            "address_state": address["state"],
            "address_zip_code": address["zip_code"],
            "address_country": address["country"],
            "created_at": created_at.isoformat(),
            "tier": tier,
            "is_active": random.random() > 0.05,  # 95% active
        }

    def _determine_tier(self, account_age_days: int) -> str:
        """Determine customer tier based on account age and randomness."""
        # Older accounts more likely to be higher tier
        if account_age_days < 30:
            return "bronze"

        tier_roll = random.random()
        age_factor = min(account_age_days / 365, 1.0)  # Cap at 1 year

        if tier_roll < 0.05 * age_factor:
            return "platinum"
        elif tier_roll < 0.15 * age_factor:
            return "gold"
        elif tier_roll < 0.35 * age_factor:
            return "silver"
        else:
            return "bronze"
