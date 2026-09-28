# PZEM2MQTT Project Makefile
# Manage PZEM004T sensor reading and MQTT publishing

.PHONY: help install uninstall run test test-simulator start stop restart status logs clean

# Default target
help:
	@echo "🔌 PZEM2MQTT Project"
	@echo ""
	@echo "📋 Available commands:"
	@echo "  make install        - Install dependencies and service"
	@echo "  make uninstall      - Remove service and cleanup"
	@echo "  make run            - Run the program directly"
	@echo "  make test           - Run all tests"
	@echo "  make test-simulator - Test with virtual hardware simulator"
	@echo ""
	@echo "🔧 Service management:"
	@echo "  make start          - Start the systemd service"
	@echo "  make stop           - Stop the systemd service"
	@echo "  make restart        - Restart the systemd service"
	@echo "  make status         - Show service status"
	@echo "  make logs           - Show service logs"
	@echo ""
	@echo "🧪 Development:"
	@echo "  make setup-dev      - Setup development environment"
	@echo "  make simulator      - Start the PZEM004T simulator"
	@echo "  make clean          - Clean temporary files"
	@echo ""
	@echo "📁 Configuration:"
	@echo "  make config         - Copy example config for editing"
	@echo "  make config-test    - Use test configuration"
	@echo "  make config-reset   - Reset to example configuration"

# Installation
install:
	@echo "🔧 Installing PZEM2MQTT..."
	sudo chmod +x scripts/install.sh
	sudo scripts/install.sh

uninstall:
	@echo "🗑️ Uninstalling PZEM2MQTT..."
	sudo chmod +x scripts/uninstall.sh
	sudo scripts/uninstall.sh

# Configuration management
config:
	@if [ ! -f config/config.json ]; then \
		echo "📝 Creating config.json from example..."; \
		cp config/config.example.json config/config.json; \
		echo "✅ Edit config/config.json to match your setup"; \
	else \
		echo "ℹ️ config/config.json already exists"; \
	fi

config-test:
	@echo "🧪 Using test configuration..."
	@if [ -f config/config.json ] && [ ! -f config/config.json.backup ]; then \
		cp config/config.json config/config.json.backup; \
		echo "💾 Original config backed up"; \
	fi
	cp config/config.test.json config/config.json
	@echo "✅ Test configuration activated"

config-reset:
	@echo "🔄 Resetting to example configuration..."
	@if [ -f config/config.json.backup ]; then \
		mv config/config.json.backup config/config.json; \
		echo "✅ Configuration restored from backup"; \
	else \
		cp config/config.example.json config/config.json; \
		echo "✅ Configuration reset to example"; \
	fi

# Running the application
run: config
	@echo "🚀 Running PZEM2MQTT..."
	cd src && python3 pzem2mqtt.py

# Service management
start:
	@echo "▶️ Starting PZEM2MQTT service..."
	sudo systemctl start pzem2mqtt.service
	@sleep 2
	@make status

stop:
	@echo "⏹️ Stopping PZEM2MQTT service..."
	sudo systemctl stop pzem2mqtt.service

restart:
	@echo "🔄 Restarting PZEM2MQTT service..."
	sudo systemctl restart pzem2mqtt.service
	@sleep 2
	@make status

status:
	@echo "📊 PZEM2MQTT service status:"
	@sudo systemctl status pzem2mqtt.service --no-pager -l || true

logs:
	@echo "📋 PZEM2MQTT service logs (press Ctrl+C to exit):"
	sudo journalctl -f -u pzem2mqtt.service

# Development and testing
setup-dev:
	@echo "🔧 Setting up development environment..."
	@echo "Installing Python dependencies..."
	pip3 install --break-system-packages -r requirements.txt || \
	(sudo apt-get update && sudo apt-get install -y python3-serial python3-pymodbus && \
	 pip3 install --break-system-packages modbus-tk paho-mqtt schedule pytz)
	@echo "Installing system dependencies..."
	sudo apt-get install -y socat
	@echo "✅ Development environment ready"

simulator:
	@echo "🎮 Starting PZEM004T simulator..."
	@echo "ℹ️ The simulator will create virtual serial ports and respond to Modbus queries"
	@echo "ℹ️ Press Ctrl+C to stop"
	cd simulator && python3 pzem_simulator.py --debug

test: setup-dev
	@echo "🧪 Running basic tests..."
	cd tests && python3 test_communication.py
	cd tests && python3 test_pzem_function.py
	@echo "✅ Basic tests completed"

test-simulator: setup-dev
	@echo "🧪 Running full simulator test..."
	@echo "ℹ️ This will setup virtual ports, start simulator, and test communication"
	chmod +x scripts/test_full.sh
	scripts/test_full.sh

# Maintenance
clean:
	@echo "🧹 Cleaning temporary files..."
	rm -f /tmp/pzem_*.log
	rm -f /tmp/pzem_test/pzem_*
	rmdir /tmp/pzem_test 2>/dev/null || true
	pkill -f "socat.*pzem" || true
	pkill -f "pzem_simulator" || true
	@echo "✅ Cleanup completed"

# Quick simulator setup for development
quick-test: setup-dev config-test
	@echo "⚡ Quick test setup..."
	@echo "1️⃣ Setting up virtual ports..."
	@chmod +x scripts/setup_virtual_ports.sh
	@scripts/setup_virtual_ports.sh
	@echo ""
	@echo "2️⃣ Starting simulator in background..."
	@cd simulator && python3 pzem_simulator.py > /tmp/pzem_simulator.log 2>&1 &
	@sleep 3
	@echo ""
	@echo "3️⃣ Testing communication..."
	@cd tests && python3 test_communication.py --port "/tmp/pzem_test/pzem_host"
	@echo ""
	@echo "✅ Quick test ready! Now run: make run"
	@echo "🛑 To stop: make clean"
