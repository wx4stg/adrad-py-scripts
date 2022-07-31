#!/usr/bin/env python3
# ADRAD New Realtime Data Processing
# Created 1 April 2022 by Sam Gardner <stgardner4@tamu.edu>

import sys
import pyart
from os import listdir, path, system, remove
from shutil import copyfile
from pathlib import Path
import numpy as np
import pandas as pd

basePath = path.dirname(path.realpath(__file__))
if len(sys.argv) > 1:
    outputDir = path.join(sys.argv[1], "TAMU")
else:
    outputDir = path.join(basePath, "output-realtime", "TAMU")


def write_radar_object_to_GR2A(rdr, filepath):
    if "prt"  not in rdr.instrument_parameters:
        # If we don't have a PRT, skip this file
        print("Unable to determine PRF from file "+file)
        return
    # Frequency is 1/period
    prf = np.round(1/np.mean(rdr.instrument_parameters["prt"]["data"]), 0)
    tmpOutputPath = path.join(basePath, "last_scan.uf")
    if path.exists(tmpOutputPath):
        remove(tmpOutputPath)
    if prf > 623.5:
        # If average PRF is greater than 623.5Hz, assume this is a volume scan
        # Use py-ART to convert sigmet->uf
        print(">>> WRITING DATA >>>")
        pyart.io.write_uf(tmpOutputPath, rdr)
        # Now we use RadxConvert to convert the tmp UF file to UF (converting py-ART UF to Radx UF allows the azimuth correction to be applied) and to L2 (converting py-ART UF to msg31 L2 for GR2Analyst users)
        # Get paths to output files
        L2outputPath = path.join(outputDir, f"TAMU_{radarScanDT.strftime('%Y%m%d')}_{radarScanDT.strftime('%H%M')}")
        print(">>> CONVERTING >>> "+file+" TO L2")
        # Create output directory if it doesn't already exist
        Path(path.dirname(L2outputPath)).mkdir(parents=True, exist_ok=True)
        # Convert tmp file to L2
        system(f"/usr/local/lrose/bin/RadxConvert -f {tmpOutputPath} -params params_L2_az-offset.txt -outdir {path.dirname(L2outputPath)} -outname {path.basename(L2outputPath)}")
    else:
        # If average PRF is less than 623.5Hz, assume this is a survey scan
        L2outputPath = path.join(outputDir, f"TAMU_{radarScanDT.strftime('%Y%m%d')}_{radarScanDT.strftime('%H%M')}")
        # Use RadxConvert to convert directly from sigmet to UF
        print(">>> CONVERTING >>> "+file+" TO UF")
        # Convert file to UF
        system(f"/usr/local/lrose/bin/RadxConvert -f {filepath} -params params_UF_az-offset.txt -outdir {path.dirname(tmpOutputPath)} -outname {path.basename(tmpOutputPath)}")
        # Now we take the converted UF file and convert it to L2
        print(">>> CONVERTING >>> "+file+" TO L2")
        # Create output directory if it doesn't already exist
        Path(path.dirname(L2outputPath)).mkdir(parents=True, exist_ok=True)
        # Convert tmp file to L2
        system(f"/usr/local/lrose/bin/RadxConvert -f {tmpOutputPath} -params l2_params.txt -outdir {path.dirname(L2outputPath)} -outname {path.basename(L2outputPath)}")

if __name__ == '__main__':
    inputPath = path.join(basePath, "input-realtime")
    filesToRead = sorted(listdir(inputPath))[-10:]
    alreadyProcDataPath = path.join(basePath, "processed.csv")
    if path.exists(alreadyProcDataPath):
        alreadyProcessed = pd.read_csv(alreadyProcDataPath)
        alreadyProcessed = alreadyProcessed["files"].tolist()
    else:
        alreadyProcessed = list()
    if path.exists(path.join(outputDir, "dir.list")):
        remove(path.join(outputDir, "dir.list"))

    for file in filesToRead:
        if file in alreadyProcessed:
            continue
        pathToRead = path.join(inputPath, file)
        copyfile(pathToRead, path.join(basePath, "input-archive", file))
        rdr = pyart.io.read(pathToRead)
        radarScanDT = pyart.util.datetime_from_radar(rdr)
        if rdr.nsweeps > 1:
            write_radar_object_to_GR2A(rdr, pathToRead)
        elif rdr.nsweeps == 1:
            if path.exists(path.join(basePath, "last_scan.uf")):
                lastRadarScan = pyart.io.read(path.join(basePath, "last_scan.uf"))
                lastRadarScanEl = np.round(lastRadarScan.fixed_angle["data"][0], 1)
                thisRadarScanEl = np.round(rdr.fixed_angle["data"][0], 1)
                if thisRadarScanEl > lastRadarScanEl and pyart.util.datetime_from_radar(rdr) > pyart.util.datetime_from_radar(lastRadarScan):
                    rdr = pyart.util.join_radar(rdr, lastRadarScan)
            write_radar_object_to_GR2A(rdr, pathToRead)
        alreadyProcessed.append(file)
        alreadyProcessedDF = pd.DataFrame(alreadyProcessed, columns=["files"])
        alreadyProcessedDF.to_csv(alreadyProcDataPath, index=False)
    
    while len(listdir(outputDir)) > 10:
        remove(path.join(outputDir, sorted(listdir(outputDir))[0]))

    dirListStr = "1 "+"\n1 ".join(sorted(listdir(outputDir)))
    with open(path.join(outputDir, "dir.list"), "w") as f:
        f.write(dirListStr)
