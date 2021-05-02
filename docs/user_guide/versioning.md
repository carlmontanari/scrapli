# Versioning

scrapli, and all scrapli related projects use [CalVer](https://calver.org) versioning standard. All release versions
 follow the format `YYYY.MM.DD`, however PyPi will shorten/standardize this to remove leading zeros.

The reason for choosing CalVer is simply to make it very clear how old a given release of scrapli is. While there are
 clearly some potential challenges around indicating when a "breaking" change occurs due to there not being the
  concept of a "major" version, this is hopefully not too big a deal for scrapli, and thus far the "core" API has
   been very stable -- there are only so many things you can/need to do over SSH after all!
 
Please also note that the [CHANGELOG](/changelog) contains notes about each version (and is updated in develop branch 
while updates are happening), and the "public" API is documented [here](/public_api_status), and includes the 
date/version of each public method's creation as well as the latest updated/modified date and any relevant notes.

A final note regarding versioning: scrapli updates are released as often as necessary/there are things to update
. This means you should ALWAYS PIN YOUR REQUIREMENTS when using scrapli!! As stated, the "core" API has been very
 stable, but things will change over time -- always pin your requirements, and keep an eye on the changelog/api docs
  -- you can "watch" this repository to ensure you are notified of any releases.
