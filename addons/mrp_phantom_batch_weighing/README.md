# MRP Phantom BoM Batch Weighing

This Odoo module allows tracking individual batch weighings of ingredients during Manufacturing Order (MO) processing when phantom BoMs are used.

## Features

- **Batch Weighing Tracking**: Record actual weights of ingredients as they are weighed in batches
- **Phantom BoM Support**: Automatically expands phantom BoMs to show all actual components
- **Multi-Session Recording**: Open the weighing wizard multiple times to record weights in different sessions (e.g., morning/afternoon batches)
- **Variance Tracking**: Automatically calculates and displays variance between theoretical and actual quantities
- **Lot/Serial Tracking**: Link weighings to specific lot or serial numbers
- **Full Traceability**: Complete audit trail of all weighing operations with user and timestamp

## Installation

1. Copy the `mrp_phantom_batch_weighing` folder to your Odoo addons directory
2. Update the apps list: Settings > Apps > Update Apps List
3. Search for "MRP Phantom BoM Batch Weighing"
4. Click Install

## Usage

### Recording Batch Weighings

1. Open a Manufacturing Order (must be in Confirmed, In Progress, or To Close state)
2. Click the **Batch Weighing** button in the header
3. The wizard will automatically populate with components from the BoM (including expanded phantom BoM components)
4. For each component:
   - The theoretical quantity is pre-filled from the BoM
   - Enter the **Actual Weight** you measured
   - Optionally add **Batch Number** and **Lot/Serial** information
   - Add **Notes** if needed
5. Click **Validate** to save the weighings

### Multi-Session Weighing

- The wizard can be opened multiple times on the same MO
- By default, it only shows components that haven't been weighed yet
- Check **Show All Components** to see and record additional weighings for already-weighed components

### Viewing Weighing History

**On Manufacturing Order:**
- Click the **Weighings** smart button to see all weighings for this MO
- View the **Batch Weighings** tab to see the complete history inline

**Global View:**
- Navigate to: Manufacturing > Operations > Batch Weighings
- Filter and group by Production Order, Product, Batch, User, or Date

## Technical Details

### Models

- `mrp.batch.weighing`: Permanent storage of weighing records
- `mrp.batch.weighing.wizard`: TransientModel for data entry
- `mrp.batch.weighing.wizard.line`: TransientModel for wizard lines

### Key Fields

- **Theoretical Quantity**: Calculated from BoM using the explode() method
- **Actual Weight**: User-entered weight measurement
- **Variance**: Calculated as (Actual - Theoretical)
- **Variance %**: Percentage variance for easy identification of discrepancies

### Variance Highlighting

- **Red (Danger)**: Variance > 10% or < -10%
- **Yellow (Warning)**: Variance between 5-10% or -5 to -10%
- **Normal**: Variance within ±5%

## Dependencies

- `mrp` (Manufacturing)
- `stock` (Inventory)

## License

LGPL-3

## Support

For issues or questions, contact your Odoo administrator.
