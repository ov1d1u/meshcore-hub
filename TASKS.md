# MeshCore Hub - Task Tracker

This document tracks implementation progress for the MeshCore Hub project. Each task can be checked off as completed.

---

## Phase 1: Foundation

### 1.1 Project Setup

- [ ] Create `pyproject.toml` with project metadata and dependencies
- [ ] Configure Python 3.11+ requirement
- [ ] Set up `src/meshcore_hub/` package structure
- [ ] Create `__init__.py` files for all packages
- [ ] Create `__main__.py` entry point

### 1.2 Development Tools

- [ ] Configure `black` formatter settings in pyproject.toml
- [ ] Configure `flake8` linting (create `.flake8` or add to pyproject.toml)
- [ ] Configure `mypy` type checking settings
- [ ] Configure `pytest` settings and test directory
- [ ] Create `.pre-commit-config.yaml` with hooks:
  - [ ] black
  - [ ] flake8
  - [ ] mypy
  - [ ] trailing whitespace
  - [ ] end-of-file-fixer
- [ ] Create `.env.example` with all environment variables

### 1.3 Common Package - Configuration

- [ ] Create `common/config.py` with Pydantic Settings:
  - [ ] `CommonSettings` (logging, MQTT connection)
  - [ ] `InterfaceSettings` (mode, serial port, mock device)
  - [ ] `CollectorSettings` (database URL, webhook settings)
  - [ ] `APISettings` (host, port, API keys)
  - [ ] `WebSettings` (host, port, network info)
- [ ] Implement environment variable loading
- [ ] Implement CLI argument override support
- [ ] Add configuration validation

### 1.4 Common Package - Database Models

- [ ] Create `common/database.py`:
  - [ ] Database engine factory
  - [ ] Session management
  - [ ] Async session support
- [ ] Create `common/models/base.py`:
  - [ ] Base model with UUID primary key
  - [ ] Timestamp mixins (created_at, updated_at)
- [ ] Create `common/models/node.py`:
  - [ ] Node model (public_key, name, adv_type, flags, first_seen, last_seen)
  - [ ] Indexes on public_key
- [ ] Create `common/models/node_tag.py`:
  - [ ] NodeTag model (node_id FK, key, value, value_type)
  - [ ] Unique constraint on (node_id, key)
- [ ] Create `common/models/message.py`:
  - [ ] Message model (receiver_node_id, message_type, pubkey_prefix, channel_idx, text, etc.)
  - [ ] Indexes for common query patterns
- [ ] Create `common/models/advertisement.py`:
  - [ ] Advertisement model (receiver_node_id, node_id, public_key, name, adv_type, flags)
- [ ] Create `common/models/trace_path.py`:
  - [ ] TracePath model (receiver_node_id, initiator_tag, path_hashes JSON, snr_values JSON)
- [ ] Create `common/models/telemetry.py`:
  - [ ] Telemetry model (receiver_node_id, node_id, node_public_key, lpp_data, parsed_data JSON)
- [ ] Create `common/models/event_log.py`:
  - [ ] EventLog model (receiver_node_id, event_type, payload JSON)
- [ ] Create `common/models/__init__.py` exporting all models

### 1.5 Common Package - Pydantic Schemas

- [ ] Create `common/schemas/events.py`:
  - [ ] AdvertisementEvent schema
  - [ ] ContactMessageEvent schema
  - [ ] ChannelMessageEvent schema
  - [ ] TraceDataEvent schema
  - [ ] TelemetryResponseEvent schema
  - [ ] ContactsEvent schema
  - [ ] SendConfirmedEvent schema
  - [ ] StatusResponseEvent schema
  - [ ] BatteryEvent schema
  - [ ] PathUpdatedEvent schema
- [ ] Create `common/schemas/nodes.py`:
  - [ ] NodeCreate, NodeRead, NodeList schemas
  - [ ] NodeTagCreate, NodeTagUpdate, NodeTagRead schemas
- [ ] Create `common/schemas/messages.py`:
  - [ ] MessageRead, MessageList schemas
  - [ ] MessageFilters schema
- [ ] Create `common/schemas/commands.py`:
  - [ ] SendMessageCommand schema
  - [ ] SendChannelMessageCommand schema
  - [ ] SendAdvertCommand schema
- [ ] Create `common/schemas/__init__.py` exporting all schemas

### 1.6 Common Package - Utilities

- [ ] Create `common/mqtt.py`:
  - [ ] MQTT client factory function
  - [ ] Topic builder utilities
  - [ ] Message serialization helpers
  - [ ] Async publish/subscribe wrappers
- [ ] Create `common/logging.py`:
  - [ ] Logging configuration function
  - [ ] Structured logging format
  - [ ] Log level configuration from settings

### 1.7 Database Migrations

- [ ] Create `alembic.ini` configuration
- [ ] Create `alembic/env.py` with async support
- [ ] Create `alembic/script.py.mako` template
- [ ] Create initial migration with all tables:
  - [ ] nodes table
  - [ ] node_tags table
  - [ ] messages table
  - [ ] advertisements table
  - [ ] trace_paths table
  - [ ] telemetry table
  - [ ] events_log table
- [ ] Test migration upgrade/downgrade

### 1.8 Main CLI Entry Point

- [ ] Create root Click group in `__main__.py`
- [ ] Add `--version` option
- [ ] Add `--config` option for config file path
- [ ] Add subcommand placeholders for: interface, collector, api, web, db

---

## Phase 2: Interface Component

### 2.1 Device Abstraction

- [ ] Create `interface/device.py`:
  - [ ] `MeshCoreDevice` class wrapping meshcore_py
  - [ ] Connection management (connect, disconnect, reconnect)
  - [ ] Get device public key via `send_appstart()`
  - [ ] Event subscription registration
  - [ ] Command sending methods
- [ ] Create `interface/mock_device.py`:
  - [ ] `MockMeshCoreDevice` class
  - [ ] Configurable event generation
  - [ ] Simulated message sending
  - [ ] Simulated network topology (optional)
  - [ ] Configurable delays and error rates

### 2.2 Receiver Mode

- [ ] Create `interface/receiver.py`:
  - [ ] `Receiver` class
  - [ ] Initialize MQTT client
  - [ ] Initialize MeshCore device
  - [ ] Subscribe to all relevant MeshCore events:
    - [ ] ADVERTISEMENT
    - [ ] CONTACT_MSG_RECV
    - [ ] CHANNEL_MSG_RECV
    - [ ] TRACE_DATA
    - [ ] TELEMETRY_RESPONSE
    - [ ] CONTACTS
    - [ ] SEND_CONFIRMED
    - [ ] STATUS_RESPONSE
    - [ ] BATTERY
    - [ ] PATH_UPDATED
  - [ ] Event handler that publishes to MQTT
  - [ ] Topic construction: `<prefix>/<pubkey>/event/<event_name>`
  - [ ] JSON serialization of event payloads
  - [ ] Graceful shutdown handling

### 2.3 Sender Mode

- [ ] Create `interface/sender.py`:
  - [ ] `Sender` class
  - [ ] Initialize MQTT client
  - [ ] Initialize MeshCore device
  - [ ] Subscribe to command topics:
    - [ ] `<prefix>/+/command/send_msg`
    - [ ] `<prefix>/+/command/send_channel_msg`
    - [ ] `<prefix>/+/command/send_advert`
    - [ ] `<prefix>/+/command/request_status`
    - [ ] `<prefix>/+/command/request_telemetry`
  - [ ] Command handlers:
    - [ ] `handle_send_msg` - send direct message
    - [ ] `handle_send_channel_msg` - send channel message
    - [ ] `handle_send_advert` - send advertisement
    - [ ] `handle_request_status` - request node status
    - [ ] `handle_request_telemetry` - request telemetry
  - [ ] Error handling and logging
  - [ ] Graceful shutdown handling

### 2.4 Interface CLI

- [ ] Create `interface/cli.py`:
  - [ ] `interface` Click command group
  - [ ] `--mode` option (receiver/sender, required)
  - [ ] `--port` option for serial port
  - [ ] `--baud` option for baud rate
  - [ ] `--mock` flag to use mock device
  - [ ] `--mqtt-host`, `--mqtt-port` options
  - [ ] `--prefix` option for MQTT topic prefix
  - [ ] Signal handlers for graceful shutdown
- [ ] Register CLI with main entry point

### 2.5 Interface Tests

- [ ] Create `tests/test_interface/conftest.py`:
  - [ ] Mock MQTT client fixture
  - [ ] Mock device fixture
- [ ] Create `tests/test_interface/test_device.py`:
  - [ ] Test connection/disconnection
  - [ ] Test event subscription
  - [ ] Test command sending
- [ ] Create `tests/test_interface/test_mock_device.py`:
  - [ ] Test mock event generation
  - [ ] Test mock command handling
- [ ] Create `tests/test_interface/test_receiver.py`:
  - [ ] Test event to MQTT publishing
  - [ ] Test topic construction
  - [ ] Test payload serialization
- [ ] Create `tests/test_interface/test_sender.py`:
  - [ ] Test MQTT to command dispatching
  - [ ] Test command payload parsing
  - [ ] Test error handling

---

## Phase 3: Collector Component

### 3.1 MQTT Subscriber

- [ ] Create `collector/subscriber.py`:
  - [ ] `Subscriber` class
  - [ ] Initialize MQTT client
  - [ ] Subscribe to all event topics: `<prefix>/+/event/#`
  - [ ] Parse topic to extract public_key and event_type
  - [ ] Route events to appropriate handlers
  - [ ] Handle connection/disconnection
  - [ ] Graceful shutdown

### 3.2 Event Handlers

- [ ] Create `collector/handlers/__init__.py`:
  - [ ] Handler registry pattern
- [ ] Create `collector/handlers/advertisement.py`:
  - [ ] Parse advertisement payload
  - [ ] Upsert node in nodes table
  - [ ] Insert advertisement record
  - [ ] Update node last_seen timestamp
- [ ] Create `collector/handlers/message.py`:
  - [ ] Parse contact/channel message payload
  - [ ] Insert message record
  - [ ] Handle both CONTACT_MSG_RECV and CHANNEL_MSG_RECV
- [ ] Create `collector/handlers/trace.py`:
  - [ ] Parse trace data payload
  - [ ] Insert trace_path record
- [ ] Create `collector/handlers/telemetry.py`:
  - [ ] Parse telemetry payload
  - [ ] Insert telemetry record
  - [ ] Optionally upsert node
- [ ] Create `collector/handlers/contacts.py`:
  - [ ] Parse contacts sync payload
  - [ ] Upsert multiple nodes
- [ ] Create `collector/handlers/event_log.py`:
  - [ ] Generic handler for events_log table
  - [ ] Handle informational events (SEND_CONFIRMED, STATUS_RESPONSE, BATTERY, PATH_UPDATED)

### 3.3 Webhook Dispatcher (Optional based on Q10)

- [ ] Create `collector/webhook.py`:
  - [ ] `WebhookDispatcher` class
  - [ ] Webhook configuration loading
  - [ ] JSONPath filtering support
  - [ ] Async HTTP POST sending
  - [ ] Retry logic with backoff
  - [ ] Error logging

### 3.4 Collector CLI

- [ ] Create `collector/cli.py`:
  - [ ] `collector` Click command
  - [ ] `--mqtt-host`, `--mqtt-port` options
  - [ ] `--prefix` option
  - [ ] `--database-url` option
  - [ ] Signal handlers for graceful shutdown
- [ ] Register CLI with main entry point

### 3.5 Collector Tests

- [ ] Create `tests/test_collector/conftest.py`:
  - [ ] In-memory SQLite database fixture
  - [ ] Mock MQTT client fixture
- [ ] Create `tests/test_collector/test_subscriber.py`:
  - [ ] Test topic parsing
  - [ ] Test event routing
- [ ] Create `tests/test_collector/test_handlers/`:
  - [ ] `test_advertisement.py`
  - [ ] `test_message.py`
  - [ ] `test_trace.py`
  - [ ] `test_telemetry.py`
  - [ ] `test_contacts.py`
- [ ] Create `tests/test_collector/test_webhook.py`:
  - [ ] Test webhook dispatching
  - [ ] Test JSONPath filtering
  - [ ] Test retry logic

---

## Phase 4: API Component

### 4.1 FastAPI Application Setup

- [ ] Create `api/app.py`:
  - [ ] FastAPI application instance
  - [ ] Lifespan handler for startup/shutdown
  - [ ] Include all routers
  - [ ] Exception handlers
  - [ ] CORS middleware configuration
- [ ] Create `api/dependencies.py`:
  - [ ] Database session dependency
  - [ ] MQTT client dependency
  - [ ] Settings dependency

### 4.2 Authentication

- [ ] Create `api/auth.py`:
  - [ ] Bearer token extraction
  - [ ] `require_read` dependency (read or admin key)
  - [ ] `require_admin` dependency (admin key only)
  - [ ] 401/403 error responses

### 4.3 Node Routes

- [ ] Create `api/routes/nodes.py`:
  - [ ] `GET /api/v1/nodes` - list nodes with pagination
    - [ ] Query params: limit, offset, search, adv_type
  - [ ] `GET /api/v1/nodes/{public_key}` - get single node
  - [ ] Include related tags in response (optional)

### 4.4 Node Tag Routes

- [ ] Create `api/routes/node_tags.py`:
  - [ ] `GET /api/v1/nodes/{public_key}/tags` - list tags
  - [ ] `POST /api/v1/nodes/{public_key}/tags` - create tag (admin)
  - [ ] `PUT /api/v1/nodes/{public_key}/tags/{key}` - update tag (admin)
  - [ ] `DELETE /api/v1/nodes/{public_key}/tags/{key}` - delete tag (admin)

### 4.5 Message Routes

- [ ] Create `api/routes/messages.py`:
  - [ ] `GET /api/v1/messages` - list messages with filters
    - [ ] Query params: type, pubkey_prefix, channel_idx, since, until, limit, offset
  - [ ] `GET /api/v1/messages/{id}` - get single message

### 4.6 Advertisement Routes

- [ ] Create `api/routes/advertisements.py`:
  - [ ] `GET /api/v1/advertisements` - list advertisements
    - [ ] Query params: public_key, since, until, limit, offset
  - [ ] `GET /api/v1/advertisements/{id}` - get single advertisement

### 4.7 Trace Path Routes

- [ ] Create `api/routes/trace_paths.py`:
  - [ ] `GET /api/v1/trace-paths` - list trace paths
    - [ ] Query params: since, until, limit, offset
  - [ ] `GET /api/v1/trace-paths/{id}` - get single trace path

### 4.8 Telemetry Routes

- [ ] Create `api/routes/telemetry.py`:
  - [ ] `GET /api/v1/telemetry` - list telemetry records
    - [ ] Query params: node_public_key, since, until, limit, offset
  - [ ] `GET /api/v1/telemetry/{id}` - get single telemetry record

### 4.9 Command Routes

- [ ] Create `api/routes/commands.py`:
  - [ ] `POST /api/v1/commands/send-message` (admin)
    - [ ] Request body: destination, text, timestamp (optional)
    - [ ] Publish to MQTT command topic
  - [ ] `POST /api/v1/commands/send-channel-message` (admin)
    - [ ] Request body: channel_idx, text, timestamp (optional)
    - [ ] Publish to MQTT command topic
  - [ ] `POST /api/v1/commands/send-advertisement` (admin)
    - [ ] Request body: flood (boolean)
    - [ ] Publish to MQTT command topic

### 4.10 Dashboard Routes

- [ ] Create `api/routes/dashboard.py`:
  - [ ] `GET /api/v1/stats` - JSON statistics
    - [ ] Total nodes count
    - [ ] Active nodes (last 24h)
    - [ ] Total messages count
    - [ ] Messages today
    - [ ] Total advertisements
    - [ ] Channel message counts
  - [ ] `GET /api/v1/dashboard` - HTML dashboard
- [ ] Create `api/templates/dashboard.html`:
  - [ ] Simple HTML template
  - [ ] Display statistics
  - [ ] Basic CSS styling
  - [ ] Auto-refresh meta tag (optional)

### 4.11 API Router Registration

- [ ] Create `api/routes/__init__.py`:
  - [ ] Create main API router
  - [ ] Include all sub-routers with prefixes
  - [ ] Add OpenAPI tags

### 4.12 API CLI

- [ ] Create `api/cli.py`:
  - [ ] `api` Click command
  - [ ] `--host` option
  - [ ] `--port` option
  - [ ] `--database-url` option
  - [ ] `--read-key` option
  - [ ] `--admin-key` option
  - [ ] `--mqtt-host`, `--mqtt-port` options
  - [ ] `--reload` flag for development
- [ ] Register CLI with main entry point

### 4.13 API Tests

- [ ] Create `tests/test_api/conftest.py`:
  - [ ] Test client fixture
  - [ ] In-memory database fixture
  - [ ] Test API keys
- [ ] Create `tests/test_api/test_auth.py`:
  - [ ] Test missing token
  - [ ] Test invalid token
  - [ ] Test read-only access
  - [ ] Test admin access
- [ ] Create `tests/test_api/test_nodes.py`:
  - [ ] Test list nodes
  - [ ] Test get node
  - [ ] Test pagination
  - [ ] Test filtering
- [ ] Create `tests/test_api/test_node_tags.py`:
  - [ ] Test CRUD operations
  - [ ] Test permission checks
- [ ] Create `tests/test_api/test_messages.py`:
  - [ ] Test list messages
  - [ ] Test filtering
- [ ] Create `tests/test_api/test_commands.py`:
  - [ ] Test send message command
  - [ ] Test permission checks
  - [ ] Test MQTT publishing

---

## Phase 5: Web Dashboard

### 5.1 FastAPI Application Setup

- [ ] Create `web/app.py`:
  - [ ] FastAPI application instance
  - [ ] Jinja2 templates configuration
  - [ ] Static files mounting
  - [ ] Lifespan handler
  - [ ] Include all routers

### 5.2 Frontend Assets

- [ ] Create `web/static/css/` directory
- [ ] Set up Tailwind CSS:
  - [ ] Create `tailwind.config.js`
  - [ ] Create source CSS with Tailwind directives
  - [ ] Configure DaisyUI plugin
  - [ ] Build pipeline (npm script or standalone CLI)
- [ ] Create `web/static/js/` directory:
  - [ ] Minimal JS for interactivity (if needed)

### 5.3 Base Template

- [ ] Create `web/templates/base.html`:
  - [ ] HTML5 doctype and structure
  - [ ] Meta tags (viewport, charset)
  - [ ] Tailwind CSS inclusion
  - [ ] Navigation header:
    - [ ] Network name
    - [ ] Links to all pages
  - [ ] Footer with contact info
  - [ ] Content block for page content

### 5.4 Home Page

- [ ] Create `web/routes/home.py`:
  - [ ] `GET /` - home page route
  - [ ] Load network configuration
- [ ] Create `web/templates/home.html`:
  - [ ] Welcome message with network name
  - [ ] Network description/details
  - [ ] Radio configuration display
  - [ ] Location information
  - [ ] Contact information (email, Discord)
  - [ ] Quick links to other sections

### 5.5 Members Page

- [ ] Create `web/routes/members.py`:
  - [ ] `GET /members` - members list route
  - [ ] Load members from JSON file
- [ ] Create `web/templates/members.html`:
  - [ ] Members list/grid
  - [ ] Member cards with:
    - [ ] Name
    - [ ] Callsign (if applicable)
    - [ ] Role/description
    - [ ] Contact info (optional)

### 5.6 Network Overview Page

- [ ] Create `web/routes/network.py`:
  - [ ] `GET /network` - network stats route
  - [ ] Fetch stats from API
- [ ] Create `web/templates/network.html`:
  - [ ] Statistics cards:
    - [ ] Total nodes
    - [ ] Active nodes
    - [ ] Total messages
    - [ ] Messages today
    - [ ] Channel statistics
  - [ ] Recent activity summary

### 5.7 Nodes Page

- [ ] Create `web/routes/nodes.py`:
  - [ ] `GET /nodes` - nodes list route
  - [ ] `GET /nodes/{public_key}` - node detail route
  - [ ] Fetch from API with pagination
- [ ] Create `web/templates/nodes.html`:
  - [ ] Search/filter form
  - [ ] Nodes table:
    - [ ] Name
    - [ ] Public key (truncated)
    - [ ] Type
    - [ ] Last seen
    - [ ] Tags
  - [ ] Pagination controls
- [ ] Create `web/templates/node_detail.html`:
  - [ ] Full node information
  - [ ] All tags
  - [ ] Recent messages (if any)
  - [ ] Recent advertisements

### 5.8 Node Map Page

- [ ] Create `web/routes/map.py`:
  - [ ] `GET /map` - map page route
  - [ ] `GET /map/data` - JSON endpoint for node locations
  - [ ] Filter nodes with location tags
- [ ] Create `web/templates/map.html`:
  - [ ] Leaflet.js map container
  - [ ] Leaflet CSS/JS includes
  - [ ] JavaScript for:
    - [ ] Initialize map centered on NETWORK_LOCATION
    - [ ] Fetch node location data
    - [ ] Add markers for each node
    - [ ] Popup with node info on click

### 5.9 Messages Page

- [ ] Create `web/routes/messages.py`:
  - [ ] `GET /messages` - messages list route
  - [ ] Fetch from API with filters
- [ ] Create `web/templates/messages.html`:
  - [ ] Filter form:
    - [ ] Message type (contact/channel)
    - [ ] Channel selector
    - [ ] Date range
    - [ ] Search text
  - [ ] Messages table:
    - [ ] Timestamp
    - [ ] Type
    - [ ] Sender/Channel
    - [ ] Text (truncated)
    - [ ] SNR
    - [ ] Hops
  - [ ] Pagination controls

### 5.10 Web CLI

- [ ] Create `web/cli.py`:
  - [ ] `web` Click command
  - [ ] `--host` option
  - [ ] `--port` option
  - [ ] `--api-url` option
  - [ ] `--api-key` option
  - [ ] Network configuration options:
    - [ ] `--network-name`
    - [ ] `--network-city`
    - [ ] `--network-country`
    - [ ] `--network-location`
    - [ ] `--network-radio-config`
    - [ ] `--network-contact-email`
    - [ ] `--network-contact-discord`
  - [ ] `--members-file` option
  - [ ] `--reload` flag for development
- [ ] Register CLI with main entry point

### 5.11 Web Tests

- [ ] Create `tests/test_web/conftest.py`:
  - [ ] Test client fixture
  - [ ] Mock API responses
- [ ] Create `tests/test_web/test_home.py`
- [ ] Create `tests/test_web/test_members.py`
- [ ] Create `tests/test_web/test_network.py`
- [ ] Create `tests/test_web/test_nodes.py`
- [ ] Create `tests/test_web/test_map.py`
- [ ] Create `tests/test_web/test_messages.py`

---

## Phase 6: Docker & Deployment

### 6.1 Dockerfile

- [ ] Create `docker/Dockerfile`:
  - [ ] Multi-stage build:
    - [ ] Stage 1: Build frontend assets (Tailwind)
    - [ ] Stage 2: Python dependencies
    - [ ] Stage 3: Final runtime image
  - [ ] Base image: python:3.11-slim
  - [ ] Install system dependencies
  - [ ] Copy and install Python package
  - [ ] Copy frontend assets
  - [ ] Set entrypoint to `meshcore-hub`
  - [ ] Default CMD (show help)
  - [ ] Health check instruction

### 6.2 Docker Compose

- [ ] Create `docker/docker-compose.yml`:
  - [ ] MQTT broker service (Eclipse Mosquitto):
    - [ ] Port mapping (1883, 9001)
    - [ ] Volume for persistence
    - [ ] Configuration file
  - [ ] Interface Receiver service:
    - [ ] Depends on MQTT
    - [ ] Device passthrough (/dev/ttyUSB0)
    - [ ] Environment variables
  - [ ] Interface Sender service:
    - [ ] Depends on MQTT
    - [ ] Device passthrough
    - [ ] Environment variables
  - [ ] Collector service:
    - [ ] Depends on MQTT
    - [ ] Database volume
    - [ ] Environment variables
  - [ ] API service:
    - [ ] Depends on Collector (for DB)
    - [ ] Port mapping (8000)
    - [ ] Database volume (shared)
    - [ ] Environment variables
  - [ ] Web service:
    - [ ] Depends on API
    - [ ] Port mapping (8080)
    - [ ] Environment variables
- [ ] Create `docker/mosquitto.conf`:
  - [ ] Listener configuration
  - [ ] Anonymous access (or auth)
  - [ ] Persistence settings

### 6.3 Health Checks

- [ ] Add health check endpoint to API:
  - [ ] `GET /health` - basic health
  - [ ] `GET /health/ready` - includes DB check
- [ ] Add health check endpoint to Web:
  - [ ] `GET /health` - basic health
  - [ ] `GET /health/ready` - includes API connectivity
- [ ] Add health check to Interface:
  - [ ] Device connection status
  - [ ] MQTT connection status
- [ ] Add health check to Collector:
  - [ ] MQTT connection status
  - [ ] Database connection status

### 6.4 Database CLI Commands

- [ ] Create `db` Click command group:
  - [ ] `meshcore-hub db upgrade` - run migrations
  - [ ] `meshcore-hub db downgrade` - rollback migration
  - [ ] `meshcore-hub db revision -m "message"` - create migration
  - [ ] `meshcore-hub db current` - show current revision
  - [ ] `meshcore-hub db history` - show migration history

### 6.5 Documentation

- [ ] Update `README.md`:
  - [ ] Project description
  - [ ] Quick start guide
  - [ ] Docker deployment instructions
  - [ ] Manual installation instructions
  - [ ] Configuration reference
  - [ ] CLI reference
- [ ] Create `docs/` directory (optional):
  - [ ] Architecture overview
  - [ ] API documentation link
  - [ ] Deployment guides

### 6.6 CI/CD (Optional)

- [ ] Create `.github/workflows/ci.yml`:
  - [ ] Run on push/PR
  - [ ] Set up Python
  - [ ] Install dependencies
  - [ ] Run linting (black, flake8)
  - [ ] Run type checking (mypy)
  - [ ] Run tests (pytest)
  - [ ] Upload coverage report
- [ ] Create `.github/workflows/docker.yml`:
  - [ ] Build Docker image
  - [ ] Push to registry (on release)

### 6.7 End-to-End Testing

- [ ] Create `tests/e2e/` directory
- [ ] Create `tests/e2e/docker-compose.test.yml`:
  - [ ] All services with mock device
  - [ ] Test database
- [ ] Create `tests/e2e/test_full_flow.py`:
  - [ ] Start all services
  - [ ] Generate mock events
  - [ ] Verify events stored in database
  - [ ] Verify API returns events
  - [ ] Verify web dashboard displays data
  - [ ] Test command flow (API -> MQTT -> Sender)

---

## Progress Summary

| Phase | Total Tasks | Completed | Progress |
|-------|-------------|-----------|----------|
| Phase 1: Foundation | 47 | 0 | 0% |
| Phase 2: Interface | 35 | 0 | 0% |
| Phase 3: Collector | 27 | 0 | 0% |
| Phase 4: API | 44 | 0 | 0% |
| Phase 5: Web Dashboard | 40 | 0 | 0% |
| Phase 6: Docker & Deployment | 28 | 0 | 0% |
| **Total** | **221** | **0** | **0%** |

---

## Notes & Decisions

### Decisions Made
*(Record architectural decisions and answers to clarifying questions here)*

- [ ] Q1 (MQTT Broker):
- [ ] Q2 (Database):
- [ ] Q3 (Web Dashboard Separation):
- [ ] Q4 (Members JSON Location):
- [ ] Q5 (Multiple Serial Devices):
- [ ] Q6 (Reconnection Strategy):
- [ ] Q7 (Mock Device Scope):
- [ ] Q8 (Event Deduplication):
- [ ] Q9 (Data Retention):
- [ ] Q10 (Webhook Configuration):
- [ ] Q11 (API Key Management):
- [ ] Q12 (Rate Limiting):
- [ ] Q13 (CORS):
- [ ] Q14 (Dashboard Authentication):
- [ ] Q15 (Real-time Updates):
- [ ] Q16 (Map Provider):
- [ ] Q17 (Tag Value Types):
- [ ] Q18 (Reserved Tag Names):
- [ ] Q19 (Health Checks):
- [ ] Q20 (Metrics/Observability):
- [ ] Q21 (Log Level Configuration):

### Blockers
*(Track any blockers or dependencies here)*

### Session Log
*(Track what was accomplished in each session)*

| Date | Session | Tasks Completed | Notes |
|------|---------|-----------------|-------|
| | | | |

