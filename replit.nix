{ pkgs }: {
  deps = [
    pkgs.python313
    pkgs.python313Packages.pip
    # PIL/Pillow image processing
    pkgs.libGL
    pkgs.libGLU
    pkgs.glib
    # Font system for PIL drawing
    pkgs.freetype
    pkgs.fontconfig
    # Postgres client lib (per psycopg2)
    pkgs.postgresql
    # General build tools
    pkgs.gcc
    pkgs.pkg-config
  ];
  env = {
    PYTHONUNBUFFERED = "1";
    LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
  };
}
