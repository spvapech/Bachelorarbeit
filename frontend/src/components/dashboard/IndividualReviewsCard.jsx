import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"

export function IndividualReviewsCard() {
    return (
        <Card className="rounded-3xl shadow-sm">
            <CardHeader>
                <CardTitle className="text-xl font-bold text-slate-800">
                    Individual Reviews (Detail View)
                </CardTitle>
            </CardHeader>

            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Date</TableHead>
                            <TableHead>Category</TableHead>
                            <TableHead>Rating</TableHead>
                            <TableHead>Comment</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        <TableRow>
                            <TableCell>12.10.2024</TableCell>
                            <TableCell>Timeliness</TableCell>
                            <TableCell>2</TableCell>
                            <TableCell className="italic">“slow response”</TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    )
}
