import { DragDropContext, Draggable, Droppable } from "@hello-pangea/dnd";
import BlockItem from "./BlockItem.jsx";

export default function BlockList({
  blocks,
  selectedId,
  onSelect,
  onChangeContent,
  onChangeType,
  onDuplicate,
  onDelete,
  onReorder,
}) {
  const handleDragEnd = (result) => {
    if (!result.destination) return;
    onReorder({
      sourceIndex: result.source.index,
      destinationIndex: result.destination.index,
    });
  };

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <Droppable droppableId="blocks">
        {(provided) => (
          <div className="block-list" ref={provided.innerRef} {...provided.droppableProps}>
            {blocks.map((block, idx) => (
              <Draggable key={block.id} draggableId={String(block.id)} index={idx}>
                {(dragProvided, snapshot) => (
                  <BlockItem
                    block={block}
                    index={idx}
                    selected={selectedId === block.id}
                    dragging={snapshot.isDragging}
                    onSelect={() => onSelect(block.id)}
                    onChangeContent={(content) => onChangeContent(block.id, content)}
                    onChangeType={(type) => onChangeType(block.id, type)}
                    onDuplicate={() => onDuplicate(block.id)}
                    onDelete={() => onDelete(block.id)}
                    dragHandleProps={dragProvided.dragHandleProps}
                    draggableProps={dragProvided.draggableProps}
                    innerRef={dragProvided.innerRef}
                  />
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </DragDropContext>
  );
}
