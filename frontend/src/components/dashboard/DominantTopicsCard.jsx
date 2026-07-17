import * as React from "react"
import { Plus } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export function DominantTopicsCard() {
    return (
        <Card className="rounded-3xl shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-xl font-bold text-slate-800">
                    Dominant Topics in Reviews (AI-based Analysis)
                </CardTitle>
                <Button variant="outline" className="rounded-full h-9 gap-2">
                    <Plus className="h-4 w-4" /> Add
                </Button>
            </CardHeader>

            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Topics</TableHead>
                            <TableHead>Frequency</TableHead>
                            <TableHead>Ø Rating</TableHead>
                            <TableHead>Sentiment</TableHead>
                            <TableHead>Example</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        <TableRow>
                            <TableCell className="font-semibold">Communication</TableCell>
                            <TableCell>High</TableCell>
                            <TableCell>2.4</TableCell>
                            <TableCell>
                                <Badge variant="destructive">Negative</Badge>
                            </TableCell>
                            <TableCell className="italic">“No reply”</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell className="font-semibold">Leadership</TableCell>
                            <TableCell>Medium</TableCell>
                            <TableCell>1.9</TableCell>
                            <TableCell>
                                <Badge variant="destructive">Negative</Badge>
                            </TableCell>
                            <TableCell className="italic">“Chaotic”</TableCell>
                        </TableRow>
                    </TableBody>
                </Table>

                <div className="mt-4 flex items-center justify-end gap-2">
                    <Button variant="outline" size="icon" className="rounded-full">
                        ‹
                    </Button>
                    <Button variant="outline" size="icon" className="rounded-full">
                        ›
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}
