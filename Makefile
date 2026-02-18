.PHONY: help install run test clean deploy-check

help:
	@echo "🚀 FocusFlow - Команды для разработки"
	@echo ""
	@echo "Доступные команды:"
	@echo "  make install       - Установить зависимости"
	@echo "  make run           - Запустить приложение локально"
	@echo "  make test          - Запустить тесты"
	@echo "  make deploy-check  - Проверить готовность к развертыванию"
	@echo "  make clean         - Очистить временные файлы"
	@echo ""

install:
	@echo "📦 Установка зависимостей..."
	cd backend && pip install -r requirements.txt
	@echo "✓ Зависимости установлены"

run:
	@echo "🚀 Запуск приложения..."
	cd backend && python app.py

test:
	@echo "🧪 Запуск тестов..."
	python test_local.py

deploy-check:
	@echo "🔍 Проверка готовности к развертыванию..."
	@if [ -f check_deployment.py ]; then \
		python check_deployment.py; \
	else \
		echo "⚠️  check_deployment.py не найден"; \
	fi

clean:
	@echo "🧹 Очистка временных файлов..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	@echo "✓ Очистка завершена"
