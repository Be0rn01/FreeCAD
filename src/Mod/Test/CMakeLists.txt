
SET(Test_SRCS
    __init__.py
    Init.py
    BaseTests.py
    Document.py
    Menu.py
    TestApp.py
    TestGui.py
    UnicodeTests.py
    UnitTests.py
    Workbench.py
    unittestgui.py
    InitGui.py
    testmakeWireString.py
    TestPythonSyntax.py
)
SOURCE_GROUP("" FILES ${Test_SRCS})

ADD_CUSTOM_TARGET(Test ALL
    SOURCES ${Test_SRCS}
)

fc_copy_sources(Test "${CMAKE_BINARY_DIR}/Mod/Test" ${Test_SRCS})

INSTALL(
    FILES
        ${Test_SRCS}
    DESTINATION
        Mod/Test
)

if(BUILD_GUI)
    add_subdirectory(Gui)
endif(BUILD_GUI)
