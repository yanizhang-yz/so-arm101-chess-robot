#!/usr/bin/env bash
# Run a Ruby script against the Xcode project using the `xcodeproj` gem that
# ships vendored inside the Homebrew CocoaPods install (it is not on the normal
# gem path). Usage: tools/xcodeproj-ruby.sh tools/some_script.rb
set -euo pipefail

POD_LIBEXEC="$(dirname "$(dirname "$(readlink -f "$(command -v pod)" 2>/dev/null || command -v pod)")")/libexec"
# Fall back to a glob if the readlink dance didn't land on libexec.
if [ ! -d "$POD_LIBEXEC/gems" ]; then
  POD_LIBEXEC="$(ls -d /opt/homebrew/Cellar/cocoapods/*/libexec 2>/dev/null | sort -V | tail -1)"
fi
RUBY="/opt/homebrew/opt/ruby/bin/ruby"
[ -x "$RUBY" ] || RUBY="ruby"

DEFAULT_PATHS="$("$RUBY" -e 'puts Gem.path.join(":")')"
export GEM_PATH="$POD_LIBEXEC:$DEFAULT_PATHS"
export LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
exec "$RUBY" "$@"
