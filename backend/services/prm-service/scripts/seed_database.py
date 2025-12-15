#!/usr/bin/env python3
"""
Master Seed Script
Orchestrates the execution of all individual seed modules in the correct order.
"""
import sys
import os
from pathlib import Path
from loguru import logger

# Add paths
script_dir = Path(__file__).parent
service_dir = script_dir.parent
backend_dir = service_dir.parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(service_dir))

# Import individual seed modules
try:
    from scripts.seed_mrns import seed_mrns
    from scripts.seed_appointments import seed_appointments
    from scripts.seed_tickets import seed_tickets
    from scripts.seed_journeys import seed_journeys
    from scripts.seed_journey_instances import seed_journey_instances
    from scripts.seed_communications import seed_communications
    from scripts.seed_clinical_data import seed_clinical_data
except ImportError as e:
    logger.error(f"Failed to import seed modules: {e}")
    # Fallback for when running directly from scripts dir
    try:
        from seed_mrns import seed_mrns
        from seed_appointments import seed_appointments
        from seed_tickets import seed_tickets
        from seed_journeys import seed_journeys
        from seed_journey_instances import seed_journey_instances
        from seed_journey_instances import seed_journey_instances
        from seed_communications import seed_communications
        from seed_clinical_data import seed_clinical_data
    except ImportError:
        logger.critical("Could not import seed modules. Ensure you are running from the correct directory.")
        sys.exit(1)

def main():
    logger.info("🚀 Starting Master Database Seed...")
    
    # 1. Foundation Additions (MRNs)
    logger.info("\n[1/6] Seeding MRNs...")
    seed_mrns()
    
    # 2. Key Clinical Data
    logger.info("\n[2/6] Seeding Appointments...")
    seed_appointments()
    
    # 3. Operational Data
    logger.info("\n[3/6] Seeding Tickets...")
    seed_tickets()

    # 4. Journey Definitions (Maps)
    logger.info("\n[4/6] Seeding Journey Definitions...")
    seed_journeys()
    
    # 5. Complex Workflows (Instances/Trips)
    logger.info("\n[5/6] Seeding Journey Instances...")
    seed_journey_instances()
    
    # 6. Communication Logs (depend on others)
    logger.info("\n[6/7] Seeding Communications...")
    seed_communications()

    # 7. Clinical Data (Observations, Medications, Reports)
    logger.info("\n[7/7] Seeding Clinical Data...")
    seed_clinical_data()
    
    logger.success("\n✨ All seed scripts executed successfully!")

if __name__ == "__main__":
    main()
