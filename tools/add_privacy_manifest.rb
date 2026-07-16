# Registers PrivacyInfo.xcprivacy in the App target so Xcode bundles it.
# Idempotent: safe to run repeatedly. Run via tools/xcodeproj-ruby.sh.
require "xcodeproj"

project_path = File.expand_path("../ios/App/App.xcodeproj", __dir__)
project = Xcodeproj::Project.open(project_path)
target = project.targets.find { |t| t.name == "App" } or abort("App target not found")

app_group = project.main_group.find_subpath("App", false) or abort("App group not found")
filename = "PrivacyInfo.xcprivacy"

ref = app_group.files.find { |f| f.path == filename } ||
      app_group.new_reference(filename)

phase = target.resources_build_phase
already = phase.files_references.include?(ref)
phase.add_file_reference(ref) unless already

project.save
puts already ? "PrivacyInfo.xcprivacy already registered — no change" \
             : "PrivacyInfo.xcprivacy registered in App target resources"
