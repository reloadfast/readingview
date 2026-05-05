.PHONY: lint type-check test security ci \
        backend-lint backend-type-check backend-test backend-security \
        frontend-lint frontend-type-check

# Backend targets
backend-lint:
	$(MAKE) -C backend lint

backend-type-check:
	$(MAKE) -C backend type-check

backend-test:
	$(MAKE) -C backend test

backend-security:
	$(MAKE) -C backend security

# Frontend targets
frontend-lint:
	cd frontend && pnpm lint

frontend-type-check:
	cd frontend && pnpm type-check

# Aggregate targets
lint: backend-lint frontend-lint

type-check: backend-type-check frontend-type-check

test: backend-test

security: backend-security

ci: lint type-check security test
