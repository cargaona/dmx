{
  description = "Simple music search and download tool using deemix.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
        
        python = pkgs.python311;
        
        
      in
      {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "dmx";
          version = "1.0.4";

          src = ./.; 

          buildInputs = [ python pkgs.makeWrapper ];
          
          installPhase = ''
            mkdir -p $out/bin $out/lib/python/dmx
            cp -r dmx/* $out/lib/python/dmx/
            cp -r *.py $out/lib/python/ 2>/dev/null || true
            
            makeWrapper ${python}/bin/python $out/bin/dmx \
              --add-flags "-m dmx" \
              --set PYTHONPATH "$out/lib/python:${python.pkgs.makePythonPath (with python.pkgs; [
                click requests colorama aiohttp deemix
              ])}"
          '';

          meta = with pkgs.lib; {
            description = "Simple music search and download tool using deemix";
            homepage = "https://github.com/cargaona/dmx";
            license = licenses.mit;
            maintainers = [ ];
            platforms = platforms.unix;
          };
        };

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/dmx";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            python.pkgs.pip
            python.pkgs.setuptools
            python.pkgs.wheel
            python.pkgs.deemix
            python.pkgs.click
            python.pkgs.colorama
            python.pkgs.requests
            python.pkgs.aiohttp
          ];

          shellHook = ''
            echo "dmx development environment"
            python --version
          '';
        };
      });
}
