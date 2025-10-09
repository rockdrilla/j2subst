ARG BASE_IMAGE
FROM ${BASE_IMAGE} AS base

## ---

FROM base AS python-ext
SHELL [ "/bin/sh", "-ec" ]

COPY /docker/scripts/*  /usr/local/sbin/

COPY /requirements.txt               /tmp/
COPY /docker/requirements-extra.txt  /tmp/

ENV PYTHON_BUILD_FROM_SOURCE='markupsafe,psutil,pyyaml'
ENV DEBIAN_DEV_PACKAGES='libffi-dev libyaml-dev'
## markupsafe, psutil
ENV CIBUILDWHEEL=1
## pyyaml
ENV PYYAML_FORCE_CYTHON=1

RUN w=$(mktemp -d) ; : "${w:?}" ; \
    { apt-mark showauto ; apt-mark showmanual ; } | sort -uV > "$w/t0" ; \
    printf '%s\n' ${DEBIAN_DEV_PACKAGES} | sort -uV > "$w/t1" ; \
    apt-install.sh ${DEBIAN_DEV_PACKAGES} ; \
    { apt-mark showauto ; apt-mark showmanual ; } | sort -uV > "$w/t2" ; \
    set +e ; \
    grep -Fxv -f "$w/t0" "$w/t2" > "$w/t3" ; \
    grep -Fxv -f "$w/t1" "$w/t3" > "$w/t4" ; \
    grep -Ev -e '-(dev|doc)$' "$w/t4" > "${PYTHON_SITE_PACKAGES}/apt-deps.txt" ; \
    set -e ; \
    rm -rf "$w/" ; unset w ; \
    apt-install.sh build-essential eatmydata ; \
    python3 -m compileall -q -j 2 /usr/local ; \
    pip-env.sh \
      pip install \
        'cython~=3.1.4' \
    ; \
    eatmydata pip-env.sh \
      pip install \
        --no-binary "${PYTHON_BUILD_FROM_SOURCE}" \
        -r /tmp/requirements.txt \
    ; \
    eatmydata pip-env.sh \
      pip install \
        --no-binary "${PYTHON_BUILD_FROM_SOURCE}" \
        -r /tmp/requirements-extra.txt \
    ; \
    pip-env.sh \
      pip uninstall -y \
        'cython' \
    ; \
    python-rm-cache.sh /usr/local ; \
    rm -rf \
      "${PYTHON_SITE_PACKAGES}/netaddr/tests" \
      "${PYTHON_SITE_PACKAGES}/psutil/tests" \
    ; \
    truncate -s 0 \
      "${PYTHON_SITE_PACKAGES}/netaddr/eui/iab.idx" \
      "${PYTHON_SITE_PACKAGES}/netaddr/eui/iab.txt" \
      "${PYTHON_SITE_PACKAGES}/netaddr/eui/oui.txt" \
      "${PYTHON_SITE_PACKAGES}/netaddr/eui/oui.idx" \
    ; \
    find "${PYTHON_SITE_PACKAGES}/" -type f -name '*.so*' -exec ls -l {} + ; \
    echo ; \
    find "${PYTHON_SITE_PACKAGES}/" -type f -name '*.so*' -printf '%p\0' \
    | sed -zE '/rust/d' \
    | sort -zuV \
    | xargs -0r strip --strip-debug --strip-unneeded ; \
    echo ; \
    find "${PYTHON_SITE_PACKAGES}/" -type f -name '*.so*' -exec ls -l {} + ; \
    apt-remove.sh build-essential ; \
    apt-clean.sh

## avoid changing already present packages
RUN rm -rfv \
      /usr/local/bin/pip \
      /usr/local/bin/pip3* \
    ; \
    find "${PYTHON_SITE_PACKAGES}/" -mindepth 1 -maxdepth 1 -printf '%P\0' \
    | sed -zEn \
      -e '/^pip(|-.+\.dist-info)$/p' \
    | env -C "${PYTHON_SITE_PACKAGES}" xargs -0r rm -rf

## ---

FROM python-ext AS pycache
SHELL [ "/bin/sh", "-ec" ]

COPY /docker/scripts/*  /usr/local/sbin/

COPY /j2subst/  ${PYTHON_SITE_PACKAGES}/j2subst/

ENV PYTHONDONTWRITEBYTECODE=''

## Python cache preseed

RUN libpython="${PYTHON_SITE_PACKAGES%/*}" ; \
    find "${libpython}/" -mindepth 1 -maxdepth 1 -printf '%P\0' \
    | sed -zEn \
      -e '/^(collections|concurrent|encodings|importlib|json|logging|multiprocessing|pathlib|re|tomllib|urllib)$/p' \
    | sort -zV \
    | env -C "${libpython}" xargs -0r \
      python3 -m compileall -q -j 2 ; \
    find "${PYTHON_SITE_PACKAGES}/" -mindepth 1 -maxdepth 1 -printf '%P\0' \
    | sed -zE \
      -e '/\.(dist-info|pth|so|txt)$/d' \
      -e '/^pip$/d' \
    | sort -zV \
    | env -C "${PYTHON_SITE_PACKAGES}" xargs -0r \
      python3 -m compileall -q -j 2

## ref: requirements-extra.txt
ENV J2SUBST_PYTHON_MODULES='netaddr psutil'

## Python cache warmup
WORKDIR "${PYTHON_SITE_PACKAGES}/j2subst/tests"

ENV J2SUBST_FN_FILTERS=1 \
    J2SUBST_QUIET=1

RUN j2subst example.j2 -
ENV PYTHONPROFILEIMPORTTIME=1
RUN j2subst example.j2 -

## Python cache adjustments
WORKDIR /usr/local
RUN d="@$(date '+%s')" ; \
    find /usr/local/lib/ -name '*.py[cdo]' -exec touch -m -d "$d" {} + ; \
    find /usr/local/lib/ -name __pycache__ -exec touch -m -d "$d" {} +

WORKDIR /pycache
RUN find /usr/local/ -type f -name '*.py[cdo]' -printf '%P\0' \
    | sort -zV \
    | tar -C /usr/local --null -T - -cf - \
    | tar -xf -

## ---

FROM base
SHELL [ "/bin/sh", "-ec" ]

COPY /docker/Dockerfile  /usr/local/share/

COPY /j2subst/  ${PYTHON_SITE_PACKAGES}/j2subst/

COPY --from=python-ext  /usr/local/bin/           /usr/local/bin/
COPY --from=python-ext  ${PYTHON_SITE_PACKAGES}/  ${PYTHON_SITE_PACKAGES}/
COPY --from=pycache     /pycache/                 /usr/local/

COPY /docker/scripts/*  /usr/local/bin/

## install missing dependencies for Python site-packages
RUN f="${PYTHON_SITE_PACKAGES}/apt-deps.txt" ; \
    [ -s "$f" ] || exit 0 ; \
    xargs -a "$f" apt-install.sh ; \
    apt-clean.sh

## ref: requirements-extra.txt
ENV J2SUBST_PYTHON_MODULES='netaddr psutil'

RUN install -d -o root -g root -m 3755 /w
VOLUME [ "/w" ]
WORKDIR /w

ENTRYPOINT [ "j2subst" ]
CMD [ ]
