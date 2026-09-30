#!/bin/sh
export DSH_HOME="${XDG_DATA_HOME}/dsh"
exec zypak-wrapper /app/main/deepseek-harness "$@"
