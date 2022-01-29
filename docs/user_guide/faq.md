# FAQ

* Question: Why build this?
    - Answer: I built `ssh2net` to learn -- to have a goal/target for writing some code. scrapli is an evolution of the
   lessons learned building ssh2net. About mid-way through building `ssh2net` I realized it may actually be kinda good
    at doing... stuff. So, sure there are other tools out there, but I think scrapli its pretty snazzy and fills in some
     of the gaps in other tools. For example scrapli is 100% compliant with strict mypy type checking, very uniformly
      documented/linted, contains a results object for every operation, is very very fast, is very flexible, and in
       general pretty awesome! Finally, while I think in general that SSH "screen scraping" is not "sexy" or even
        "good", it is the lowest common denominator for automation in the networking world. So I figured I could try
         to make the fastest, most flexible library around for SSH network automation! 
* Question: Is this better than XYZ?
    - Answer: Nope! It is different though! The main focus is just to be stupid fast. It is very much that. It 
     *should* be
  super reliable too as the timeouts are very easy/obvious to control, and it should also be very very very easy to
   adapt to any other network-y type CLI by virtue of flexible prompt finding and easily modifiable on connect
    functions.
* I wanna go fast!
    - Hmmm... not a question but I dig it. If you wanna go fast you gotta learn to drive with the fear... ok, enough
   Talladega Nights quoting for now. In theory using the `ssh2` transport is the gateway to speed... being a very
    thin wrapper around libssh2 means that its basically all C and that means its probably about as fast as we're
     reasonably going to get. All that said, scrapli by default uses the `system` transport which is really just
      using your system ssh.... which is almost certainly libssh2/openssh which is also C. There is a thin layer of
       abstraction between scrapli and your system ssh but really its just reading/writing to a file which Python
        should be doing in C anyway I would think. In summary... while `ssh2` is probably the fastest you can go with
         scrapli, the difference between `ssh2` and `system` transports in limited testing is very small, and the
          benefits of using system transport (native ssh config file support!!) probably should outweigh the speed of
           ssh2 -- especially if you have control persist and can take advantage of that with system transport!
* Hey does this thing do SCP?
     - Nope! But the very cool @viktorkertesz has created [scrapli_scp](https://github.com/viktorkertesz/scrapli_scp)
       which you should defo check out if you wanna do SCP things!
* Other questions? Ask away!
