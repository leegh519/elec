import Foundation
import Vision
import AppKit

struct OCRLine: Codable {
    let text: String
    let confidence: Float
    let x: Double
    let y: Double
    let width: Double
    let height: Double
}

struct OCRResult: Codable {
    let imageWidth: Int
    let imageHeight: Int
    let lines: [OCRLine]
}

guard CommandLine.arguments.count == 2 else {
    fputs("usage: vision_ocr <image-path>\n", stderr)
    exit(2)
}

let imageURL = URL(fileURLWithPath: CommandLine.arguments[1])
guard let image = NSImage(contentsOf: imageURL),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    fputs("failed to load image\n", stderr)
    exit(3)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = ["ko-KR", "en-US"]
request.minimumTextHeight = 0.006

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([request])
} catch {
    fputs("OCR failed: \(error)\n", stderr)
    exit(4)
}

let observations = request.results ?? []
let lines: [OCRLine] = observations.compactMap { observation in
    guard let candidate = observation.topCandidates(1).first else { return nil }
    let box = observation.boundingBox
    return OCRLine(
        text: candidate.string,
        confidence: candidate.confidence,
        x: box.origin.x,
        y: 1.0 - box.origin.y - box.height,
        width: box.width,
        height: box.height
    )
}.sorted {
    if abs($0.y - $1.y) > 0.003 { return $0.y < $1.y }
    return $0.x < $1.x
}

let result = OCRResult(imageWidth: cgImage.width, imageHeight: cgImage.height, lines: lines)
let encoder = JSONEncoder()
encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
let data = try encoder.encode(result)
FileHandle.standardOutput.write(data)
FileHandle.standardOutput.write(Data("\n".utf8))
