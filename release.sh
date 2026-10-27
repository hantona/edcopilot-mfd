# Run a Windows and Linux build with the current git tag appended to the archive names

tag_count="$(git tag --points-at HEAD |wc -l)"
if [[ "${tag_count}" != "1" ]] ; then
  echo "A single git tag is required for release"
  exit 1
fi

version="$(git tag --points-at HEAD)"

if [[ -z "${version}" ]] ; then
  echo "No version detected from git tag"
  exit 1
fi
echo "Building installer bundles for $version"
echo "Running Linux build"
./build.sh "$version"

echo "Running Windows Build"
cmd.exe /c build.bat "$version"