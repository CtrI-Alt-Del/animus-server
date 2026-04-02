# [1.10.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.9.0...v1.10.0) (2026-04-01)


### Bug Fixes

* **auth:** ANI-29 restore legacy account profile route ([15690a6](https://github.com/CtrI-Alt-Del/animus-server/commit/15690a61d2685b6450fd5cfab71a303aacdb1988))


### Features

* **intake:** ANI-29 add analysis management endpoints ([d40c4db](https://github.com/CtrI-Alt-Del/animus-server/commit/d40c4dbdc5ec20383621a413674270018635766f))
* **intake:** ANI-29 add validation for limit parameter in analysis listing ([18ec896](https://github.com/CtrI-Alt-Del/animus-server/commit/18ec896c8005f0ce5c92823bd6eb339d7f2e3570))
* **intake:** ANI-29 implement analysis management endpoints and update pagination response handling ([7b49c5a](https://github.com/CtrI-Alt-Del/animus-server/commit/7b49c5ae25bc346269c593231d20f3f7ae27cd73))

# [1.9.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.8.0...v1.9.0) (2026-03-31)


### Bug Fixes

* ANI-53 handle missing account in GetAccountUseCase ([c9fc75c](https://github.com/CtrI-Alt-Del/animus-server/commit/c9fc75ce9b8fef22fce0b15cfcb3cb93fa60fe45))
* ANI-53 resolve copilot review issues on account endpoint ([7b4842f](https://github.com/CtrI-Alt-Del/animus-server/commit/7b4842f954cc40ffa14d2db26527c91fe0f463b0))
* **auth:** ANI-53 align repository contract and remove unused import ([d0ee6c1](https://github.com/CtrI-Alt-Del/animus-server/commit/d0ee6c1cfa4f09a48c7913e080c1af29bc537ed0))


### Features

* **auth:** ANI-53 add auth/me endpoint to retrieve user details ([3956b38](https://github.com/CtrI-Alt-Del/animus-server/commit/3956b38c8f450a8b9ae4ddb6ec1b499f5392d5bb))

# [1.8.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.7.0...v1.8.0) (2026-03-31)


### Features

* **intake:** ANI-44 add signed url endpoint ([66fb76f](https://github.com/CtrI-Alt-Del/animus-server/commit/66fb76f480352b5ba8729f21351cf05c0840f1be))

# [1.7.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.6.0...v1.7.0) (2026-03-31)


### Features

* ANI-48 add analysis petitions intake endpoint ([079d050](https://github.com/CtrI-Alt-Del/animus-server/commit/079d0507e61fea2c55335e4e8923225d467a2e90))
* ANI-48 implement intake precedents search and summary contracts ([758f3e7](https://github.com/CtrI-Alt-Del/animus-server/commit/758f3e7f44256e01ef31ae503d97ce9e7bb742f7))

# [1.6.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.5.0...v1.6.0) (2026-03-28)


### Bug Fixes

* ANI-45 resolve Ruff B023 and typing cast lint issues ([3556568](https://github.com/CtrI-Alt-Del/animus-server/commit/3556568de06fe45c95422bd013e71a398c05451e))


### Features

* ANI-45 add petition endpoints and summary flow ([6c48352](https://github.com/CtrI-Alt-Del/animus-server/commit/6c48352d55001d18b2d8e5366307f657a065bce8))
* ANI-45 implement precedent vectorization pipeline ([e9a15a5](https://github.com/CtrI-Alt-Del/animus-server/commit/e9a15a5daab249f566c780a199c380d3732e5e4b))

# [1.5.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.4.0...v1.5.0) (2026-03-28)


### Bug Fixes

* ANI-47 fix test speed ([f38073c](https://github.com/CtrI-Alt-Del/animus-server/commit/f38073c059f4cd06dfdd4e506f0efe49aa2bc219))
* ANI-47 fixed linter problems ([29cb106](https://github.com/CtrI-Alt-Del/animus-server/commit/29cb10685999c3cec68160494a761fb75e3999da))


### Features

* **intake:** ANI-47 add qdrant provider ([445aaef](https://github.com/CtrI-Alt-Del/animus-server/commit/445aaefeb83e65aaa4065bbb24713ffbaeafa35c))
* **intake:** ANI-47 add vectorize precedents job ([04a792a](https://github.com/CtrI-Alt-Del/animus-server/commit/04a792a1a710aaa9c1bfff907c7aeaea78421430))
* **intake:** ANI-47 finish vetorization job ([3a11469](https://github.com/CtrI-Alt-Del/animus-server/commit/3a11469681514d725d856d9d6aa76b9d919d2838))

# [1.4.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.3.0...v1.4.0) (2026-03-26)


### Bug Fixes

* ANI-57 address otp review feedback ([99d227f](https://github.com/CtrI-Alt-Del/animus-server/commit/99d227f7d58dcfc8aeb7b2af1c9d8281f799736b))
* ANI-57 enforce optional repository lookups and otp attempt limits ([8d0e30b](https://github.com/CtrI-Alt-Del/animus-server/commit/8d0e30b5727c6a255bad7e3b36fd65bb58b22fb9))
* ANI-57 reset verification attempts when generating otp ([d68c832](https://github.com/CtrI-Alt-Del/animus-server/commit/d68c8325383736733ee680472891da35c25f1e73))


### Features

* ANI-57 add auth seeding flow with faker support ([4a69c62](https://github.com/CtrI-Alt-Del/animus-server/commit/4a69c628918b1f4fb915017a64282c6129a8596a))
* ANI-57 add Dockerfile for multi-stage build with uvicorn setup ([756aafe](https://github.com/CtrI-Alt-Del/animus-server/commit/756aafe6f731d0c7340ac7a6d7ef4798da9168f6))
* ANI-57 implement otp email verification flow ([6cfa3c3](https://github.com/CtrI-Alt-Del/animus-server/commit/6cfa3c36656011353e181764d7d81776158370bc))

# [1.3.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.2.0...v1.3.0) (2026-03-25)


### Bug Fixes

* ANI-34 resolve PR review findings on naming and docs ([32f8d87](https://github.com/CtrI-Alt-Del/animus-server/commit/32f8d87f30a96923553a85dd19b0e9874e20c586))


### Features

* **auth:** ANI-34 add email/password sign-in endpoint and domain errors ([eb7035c](https://github.com/CtrI-Alt-Del/animus-server/commit/eb7035cccdf9edc0401a9798d2e0255c0e56a9bd))

# [1.2.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.1.0...v1.2.0) (2026-03-24)


### Features

* **auth:** #ANI-37 add sign in with google oauth ([aadbc4a](https://github.com/CtrI-Alt-Del/animus-server/commit/aadbc4a9906f44acc02310bb5ea75591e5210af6)), closes [#ANI-37](https://github.com/CtrI-Alt-Del/animus-server/issues/ANI-37)

# [1.1.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.0.0...v1.1.0) (2026-03-23)


### Features

* **docs:** #ANI-56 add swagger docs ([f7cea7d](https://github.com/CtrI-Alt-Del/animus-server/commit/f7cea7d153f2086735a89c231f259bc4e00185ba)), closes [#ANI-56](https://github.com/CtrI-Alt-Del/animus-server/issues/ANI-56)

# 1.0.0 (2026-03-23)


### Bug Fixes

* ANI-21 resolve PR review feedback across core, docs, and tooling ([3d26712](https://github.com/CtrI-Alt-Del/animus-server/commit/3d26712095ff5325c6972d25ad0f52f555aad561))
* ANI-25 update PostgreSQL port mapping in docker-compose.yaml ([6027092](https://github.com/CtrI-Alt-Del/animus-server/commit/6027092345d2bcd2c03986e28bdc6e5cf786c5ec))


### Features

* ANI-21 bootstrap animus server structure and documentation ([b3c326e](https://github.com/CtrI-Alt-Del/animus-server/commit/b3c326e065e1099ff6aca65604096ef6be6342da))
* **auth:** ANI-35 implement sign-up workflow with persistence and email verification ([96b3516](https://github.com/CtrI-Alt-Del/animus-server/commit/96b35163f8f62fe623f65193f3937e9404677a0f))
* **auth:** ANI-52 add auth domain entities structures and interfaces ([60fbbab](https://github.com/CtrI-Alt-Del/animus-server/commit/60fbbab3a562bf96982025bd809b838ed700edcd))
* **intake:** ANI-52 add intake domain entities structures and interfaces ([a01b9f8](https://github.com/CtrI-Alt-Del/animus-server/commit/a01b9f813631aa137c5dac02b76e9d5e4aae5121))
* **storage:** ANI-52 add storage structures and provider interfaces ([473cf57](https://github.com/CtrI-Alt-Del/animus-server/commit/473cf57fab00bdaea205fc25b6364e74eff236a5))
