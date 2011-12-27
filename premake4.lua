if _ACTION == "clean" then
    -- clean up manually generated files
    os.execute "rm -f sample.database"
    os.execute "rm -f test.database"
    os.execute "rm -f src/test/AllTests.c"
else
    -- manually generate files
    os.execute "./generate-sample-dbs.sh"
    os.execute "./gen-tests.sh"
end

solution "graphpaper"
    language "C"
    configurations {"release", "debug"}
    includedirs "src/cutest"
    project "graphpaper"
        files "src/graphpaper/**.c"
        kind "StaticLib"
    project "test"
        files {"src/cutest/CuTest.c", "src/test/**.c"}
        kind "ConsoleApp"
        links {"graphpaper", "dl", "pthread"}

