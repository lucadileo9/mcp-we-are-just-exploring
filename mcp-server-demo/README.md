# MCP Server Demo

This is a demo MCP server.

## Proposed appointment Management Tools

This server could be extended to support appointment management with the following tools:

### `create_appointment`
**Description**: Create a new appointment.
**Arguments**:
- `title` (string): The title of the appointment.
- `description` (string, optional): Detailed description of the appointment.
- `priority` (string, optional): Priority level (e.g., "low", "medium", "high").

### `list_appointments`
**Description**: List all appointments, optionally filtered by status or priority.
**Arguments**:
- `status` (string, optional): Filter by status (e.g., "pending", "completed").
- `priority` (string, optional): Filter by priority.

### `update_appointment`
**Description**: Update an existing appointment.
**Arguments**:
- `appointment_id` (string): The ID of the appointment to update.
- `status` (string, optional): New status.
- `priority` (string, optional): New priority.
- `description` (string, optional): New description.

### `complete_appointment`
**Description**: Mark a appointment as completed.
**Arguments**:
- `appointment_id` (string): The ID of the appointment to complete.

### `delete_appointment`
**Description**: Delete a appointment.
**Arguments**:
- `appointment_id` (string): The ID of the appointment to delete.

### `search_appointments`
**Description**: Search for appointments by keyword.
**Arguments**:
- `query` (string): The search query.